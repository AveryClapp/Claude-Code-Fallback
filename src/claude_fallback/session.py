"""Session management and mode switching logic."""

import fcntl
import os
import pty
import signal
import struct
import sys
import termios
import time
from subprocess import Popen

from rich.console import Console

from claude_fallback.config import Config
from claude_fallback.monitor import Monitor

console = Console()


class Session:
    """Manages the Claude Code session and handles mode switching."""

    def __init__(self, config: Config):
        self.config = config
        self.process = None
        self.monitor = None
        self.master_fd = None  # PTY master file descriptor
        self.current_mode = "subscription"  # "subscription" or "api"
        self.current_dir = os.getcwd()
        self.old_tty_settings = None

    def start(self):
        """Start Claude Code in subscription mode with interactive PTY."""
        console.print("[bold green]Starting Claude Code in subscription mode...[/bold green]")

        # Start Claude Code without API key (subscription mode)
        env = os.environ.copy()
        # Make sure ANTHROPIC_API_KEY is not set initially
        env.pop('ANTHROPIC_API_KEY', None)

        # Use pty.fork() to create a pseudo-terminal
        # This allows the user to interact with Claude Code while we monitor output
        pid, self.master_fd = pty.fork()

        if pid == 0:  # Child process
            # Execute Claude Code in the child process
            os.execvpe('claude', ['claude'], env)
        else:  # Parent process
            # Set the PTY size to match the current terminal
            self._set_pty_size(self.master_fd)

            # Store the process (we track it via pid)
            self.process = self._get_process_from_pid(pid)

            # Set up monitor with the PTY file descriptor
            self.monitor = Monitor(self.process, self.master_fd)
            self.monitor.start()

            console.print("[dim]Session started. Monitoring for usage limits...[/dim]")

    def _set_pty_size(self, fd):
        """Set the PTY size to match the current terminal."""
        try:
            # Get the size of the current terminal
            size = struct.unpack('HHHH', fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
            # Set the PTY to the same size
            fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', *size))
        except Exception:
            # If we can't get/set the size, just continue
            pass

    def _get_process_from_pid(self, pid):
        """Create a process-like object from PID for monitoring."""
        class ProcessWrapper:
            def __init__(self, pid):
                self.pid = pid

            def poll(self):
                """Check if process is still running."""
                try:
                    os.kill(self.pid, 0)
                    return None  # Process is running
                except OSError:
                    return -1  # Process has exited

            def terminate(self):
                """Send SIGTERM to process."""
                try:
                    os.kill(self.pid, signal.SIGTERM)
                except OSError:
                    pass

            def kill(self):
                """Send SIGKILL to process."""
                try:
                    os.kill(self.pid, signal.SIGKILL)
                except OSError:
                    pass

            def wait(self, timeout=None):
                """Wait for process to exit."""
                try:
                    os.waitpid(self.pid, 0)
                except OSError:
                    pass

        return ProcessWrapper(pid)

    def switch_to_api_mode(self):
        """Switch from subscription to API mode by restarting the process."""
        if self.current_mode == "api":
            console.print("[yellow]Already in API mode[/yellow]")
            return

        console.print("\n[bold yellow]⚠ Usage limit reached![/bold yellow]")

        # Prompt user if configured to do so
        if self.config.prompt_before_switch:
            console.print("[yellow]Switch to API billing to continue?[/yellow]")
            response = input("Continue with API? (y/n): ")
            if response.lower() != 'y':
                console.print("[red]Switch cancelled. Exiting...[/red]")
                self.stop()
                return

        console.print("[bold yellow]Switching to API mode...[/bold yellow]")

        # Stop current monitor
        if self.monitor:
            self.monitor.stop()

        # Close old PTY
        if self.master_fd is not None:
            os.close(self.master_fd)

        # Terminate current process gracefully
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                # Force kill if it doesn't terminate
                self.process.kill()

        # Set up environment with API key
        env = os.environ.copy()
        env['ANTHROPIC_API_KEY'] = self.config.api_key

        # Restart Claude Code with API key using PTY
        console.print("[dim]Restarting Claude Code with API key...[/dim]")

        pid, self.master_fd = pty.fork()

        if pid == 0:  # Child process
            os.execvpe('claude', ['claude'], env)
        else:  # Parent process
            # Set the PTY size to match the current terminal
            self._set_pty_size(self.master_fd)

            self.process = self._get_process_from_pid(pid)

            # Update mode and restart monitor
            self.current_mode = "api"
            self.monitor = Monitor(self.process, self.master_fd)
            self.monitor.start()

            console.print("[bold green]✓ Switched to API mode[/bold green]")

    def wait(self):
        """
        Main loop - forward user input to Claude Code and monitor for events.

        This handles bidirectional communication:
        - User input → Claude Code (via PTY)
        - Claude Code output → User (via Monitor thread)
        """
        import select
        import tty

        # Set up signal handler for terminal resize
        def handle_sigwinch(signum, frame):
            if self.master_fd is not None:
                self._set_pty_size(self.master_fd)

        old_sigwinch = signal.signal(signal.SIGWINCH, handle_sigwinch)

        # Set terminal to raw mode for proper interaction
        try:
            self.old_tty_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        except:
            pass

        try:
            while True:
                # Check monitor status
                status = self.monitor.get_status()

                if status == "exited":
                    console.print("\n[dim]Claude Code session ended[/dim]")
                    break
                elif status == "switch":
                    # Restore terminal before prompting
                    self._restore_terminal()
                    self.switch_to_api_mode()
                    self.monitor.reset_switch_flag()
                    # Set raw mode again if we're continuing
                    if self.process and self.process.poll() is None:
                        try:
                            tty.setraw(sys.stdin.fileno())
                        except:
                            pass

                # Forward user input to Claude Code
                if self.master_fd is not None:
                    # Check if user has typed something (non-blocking)
                    if select.select([sys.stdin], [], [], 0)[0]:
                        try:
                            data = os.read(sys.stdin.fileno(), 1024)
                            if data:
                                os.write(self.master_fd, data)
                        except OSError:
                            break

                time.sleep(0.01)  # Small sleep to avoid busy-waiting

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        finally:
            # Restore signal handler
            signal.signal(signal.SIGWINCH, old_sigwinch)
            self._restore_terminal()
            self.stop()

    def _restore_terminal(self):
        """Restore terminal to normal mode."""
        if self.old_tty_settings is not None:
            try:
                import termios
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_tty_settings)
            except:
                pass

    def stop(self):
        """Clean shutdown of session."""
        console.print("[dim]Stopping session...[/dim]")

        if self.monitor:
            self.monitor.stop()

        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except:
                pass

        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except:
                self.process.kill()

        console.print("[green]Session stopped[/green]")

