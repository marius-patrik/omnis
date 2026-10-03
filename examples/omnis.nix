# OmnisOS v0 reference configuration.
# This file demonstrates the frozen option families from docs/IMPLEMENTATION.md.
{ config, pkgs, ... }:
{
  omnis = {
    enable = true;

    graph = {
      enable = true;
      dataDir = "/var/lib/omnis/graph";
      socket = "/run/omnis/graph.sock";
      sqlite = {
        journalMode = "wal";
        synchronous = "full";
      };
    };

    os = {
      enable = true;
      observe = {
        systemd = true;
        udev = true;
        rtnetlink = true;
        processes = true;
        watchedFileScopes = [ ];
      };
    };

    manager = {
      enable = true;
      socket = "/run/omnis/manager.sock";
      nixControlSocket = "/run/omnis/nix-control.sock";
      discovery.enable = true;

      providers = {
        nix.enable = true;
        cli.enable = true;
        systemd.enable = true;
        http.enable = true;
        mcp.enable = true;
        models.openaiCompatible.enable = false;
        models.anthropic.enable = false;
        models.llamaCpp.enable = false;
        models.onnx.enable = false;
        harnesses.claude.enable = false;
        harnesses.codex.enable = false;
        harnesses.opencode.enable = false;
      };
    };

    agent.users.alice = {
      enable = true;
      # Defaults below $XDG_STATE_HOME/omnis/agent for the user.
      memory = {
        fts5 = true;
        vectorIndex = "sqlite-vec";
      };
    };

    control.users.alice = {
      enable = true;
      defaultMode = "2d";
      shell = pkgs.zsh;
      xwayland.enable = true;
      scrollbackLines = 100000;
    };

    hosts = {
      nativeRemote.enable = true;
      quic.enable = true;
      quic.port = 7443;
    };

    security = {
      protectedHandles.enable = true;
      systemdCredentials.enable = true;
      executionIsolation.enable = true;
      defaultWorkerNetwork = "deny";
    };
  };
}
