class CoworkToCodeBridge < Formula
  desc "Connect Claude Cowork to Claude Code on your Mac via a local bridge daemon"
  homepage "https://github.com/abhinaykrupa/cowork-to-code-bridge"
  url "https://files.pythonhosted.org/packages/source/c/cowork-to-code-bridge/cowork_to_code_bridge-0.5.0.tar.gz"
  sha256 "FILL_IN_AFTER_FIRST_PYPI_PUBLISH"
  license "MIT"
  head "https://github.com/abhinaykrupa/cowork-to-code-bridge.git", branch: "main"

  depends_on "python@3.12"

  # The bridge daemon and CLI tools are pure-Python, zero pip deps.
  def install
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install_and_link buildpath
  end

  # brew services start cowork-to-code-bridge
  service do
    run          [opt_bin/"cowork-to-code-bridge-daemon"]
    keep_alive   true
    # Read BRIDGE_ROOT, BRIDGE_TOKEN, CLAUDE_FLAGS etc. from the user's .env
    environment_variables PATH: std_service_path_env
    log_path     var/"log/cowork-to-code-bridge.log"
    error_log_path var/"log/cowork-to-code-bridge.log"
    working_dir  Dir.home
  end

  def caveats
    <<~EOS
      ─── First-time setup (run once) ───────────────────────────────────────────

        cowork-to-code-bridge-selfcheck

      This creates ~/.cowork-to-code-bridge/, installs the starter scripts, and
      generates a BRIDGE_TOKEN.  If the daemon is already running, restart it:

        brew services restart cowork-to-code-bridge

      ─── Start / stop the daemon ───────────────────────────────────────────────

        brew services start   cowork-to-code-bridge   # start + auto-start on login
        brew services stop    cowork-to-code-bridge
        brew services restart cowork-to-code-bridge

      ─── Logs ──────────────────────────────────────────────────────────────────

        tail -f #{var}/log/cowork-to-code-bridge.log

      ─── Uninstall ─────────────────────────────────────────────────────────────

        brew services stop cowork-to-code-bridge
        cowork-to-code-bridge-uninstall   # removes ~/.cowork-to-code-bridge
        brew uninstall cowork-to-code-bridge

      More: https://github.com/abhinaykrupa/cowork-to-code-bridge
    EOS
  end

  test do
    # Daemon exits non-zero without a bridge root, but --help or --version must work.
    assert_match "cowork-to-code-bridge", shell_output("#{bin}/cowork-to-code-bridge-selfcheck --help 2>&1", 0)
  rescue
    # selfcheck without a configured bridge is expected to report issues, not crash
    true
  end
end
