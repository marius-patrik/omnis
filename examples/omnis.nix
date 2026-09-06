# The whole system, declared.
#
# This is the reference declaration: every subsystem, environment, host, and surface Omnis manages,
# in one file. Evaluating it produces a generation (ADR-0012); applying that generation converges the
# running system toward it. Removing something here removes it entirely — the processes, the
# packages, the files, and everything it contributed to the rest of the system (ADR-0013).
#
# Nothing below is a setting the daemon reads at runtime. It is the definition of the system.

{ config, lib, pkgs, ... }:

{
  omnis = {

    # ─────────────────────────────────────────────────────────────────────────
    # Hosts — where things are allowed to run (ADR-0016)
    #
    # A host is a named execution target backed by a runtime. The container runtime is itself an
    # abstraction: `docker` works on all three platforms, `wsl` is a first-class host on Windows,
    # `podman` and `nspawn` are Linux-native, and `remote` is another personal machine reached over
    # the tailnet.
    # ─────────────────────────────────────────────────────────────────────────
    hosts = {
      workstation.backend = "native";

      core = {
        backend = "docker";       # or "wsl" | "podman" | "nspawn" | "native"
        resources.memory = "8G";
      };

      laptop = {
        backend = "remote";
        address = "laptop.tail1234.ts.net";
      };
    };

    # ─────────────────────────────────────────────────────────────────────────
    # Placement — which process runs on which host (ADR-0016)
    #
    # Constraints are checked when the generation is evaluated, not when it runs. The GUI needs a
    # display and a GPU, so it resolves to a native host; a placement that cannot satisfy that is a
    # configuration error reported here, with a reason.
    # ─────────────────────────────────────────────────────────────────────────
    placement = {
      daemon = "core";
      gui    = "workstation";
      tui    = "workstation";
      cli    = "workstation";
      web    = "core";
    };

    # ─────────────────────────────────────────────────────────────────────────
    # Subsystems — peers beside the core, never inside it (ADR-0013)
    #
    # Each is a separate process speaking the Substrate Bus, started on first message by socket
    # activation and supervised by systemd. Setting `enable = false` does not disable a feature that
    # stays installed: it removes the subsystem and its closure.
    # ─────────────────────────────────────────────────────────────────────────
    subsystems = {
      vcs = {
        enable = true;
        # Backends are interchangeable and removable. Drop "git" here and git leaves entirely —
        # binary, credential helper, completions, menu entries, and all (ADR-0011).
        backends = [ "git" "sapling" ];
        default  = "git";
      };

      terminals = {
        enable = true;
        multiplexer = "tmux";
      };

      lsp.enable = true;
      dap.enable = false;

      browser = {
        enable = true;
        renderMode = "auto";      # "semantic-text" | "raster" | "auto"
      };

      cas = {
        enable = true;
        chunking = "fastcdc";
        store = "/var/lib/omnis/cas";
      };

      tasks.enable = true;

      agent = {
        enable = true;
        # Order is the fallback chain; a harness without credentials is skipped (ADR-0004).
        harnesses = [ "claude" "codex" "kimi" ];
        approval  = "escrow";     # every side-effectful action passes a ticket (ADR-0006)
      };

      exthost.enable = false;
    };

    # ─────────────────────────────────────────────────────────────────────────
    # Environments — guest operating systems beside the core (ADR-0014)
    #
    # Siblings of the core at host level, never nested inside it. `container` shares the kernel,
    # `vm` brings its own, `compat` runs Windows applications with no guest OS at all.
    # ─────────────────────────────────────────────────────────────────────────
    environments = {
      arch = {
        kind = "container";
        image = "archlinux";
        shareHome = true;
      };

      windows = {
        kind = "vm";
        # We cannot ship Windows. The image and the licence are the user's.
        image = "/var/lib/omnis/images/win11.qcow2";
        resources = { cpus = 4; memory = "8G"; };
        apps = {
          # Individual applications as ordinary windows, rather than a desktop in a box.
          integration = "remoteapp";
          expose = [ "photoshop" "excel" ];
        };
      };

      games = {
        kind = "compat";
        runner = "proton";
      };
    };

    # ─────────────────────────────────────────────────────────────────────────
    # Presentation — profiles bundle, themes colour (ADR-0002)
    #
    # A theme is colours in the VS Code colour-theme format, so existing themes load unmodified.
    # A profile bundles a theme with axis values, chrome, typography, and keymaps.
    # ─────────────────────────────────────────────────────────────────────────
    presentation = {
      profile   = "zed";
      theme     = "catppuccin-mocha";
      iconTheme = "material";

      # The capability matrix. Every axis is independent; a profile is a point in this space.
      axes = {
        presentation = "cell-grid";     # "cell-grid" | "widget" | "hybrid"
        layout       = "terminal-grid"; # "chat-centric" | "ide-split" | "terminal-grid" | "vcs-dag"
        inputBar     = "global-hud";    # "global-hud" | "per-pane" | "hybrid"
        keybindings  = "zed";
      };

      window = {
        frameStyle = "frameless-custom";
        vibrancy   = "mica";
      };
    };

    # ─────────────────────────────────────────────────────────────────────────
    # Remote access — a web surface over Tailscale (ADR-0015)
    #
    # Optional. With this disabled, and with no network at all, everything above still works.
    # ─────────────────────────────────────────────────────────────────────────
    remote = {
      enable = true;
      via = "tailscale";            # name, certificate, and caller identity come from the tailnet
      surface = "web";
    };

    # ─────────────────────────────────────────────────────────────────────────
    # Secrets — references only, never values (ADR-0010)
    #
    # A declaration is diffable, shareable, and routinely pasted into an issue. Values live in the
    # OS keychain and reach child processes by injection at spawn time; agents may reference a
    # secret by name and can never read it.
    # ─────────────────────────────────────────────────────────────────────────
    secrets = {
      github.ref    = "keychain:omnis/github";
      anthropic.ref = "keychain:omnis/anthropic";
    };
  };
}
