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
        models.openaiCompatible.enable = true;
        models.anthropic.enable = true;
        models.llamaCpp.enable = true;
        models.onnx.enable = true;
        harnesses.claude.enable = true;
        harnesses.codex.enable = true;
        harnesses.opencode.enable = true;
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
    };

    hosts = {
      nativeRemote.enable = true;
      quic.enable = true;
    };

    security = {
      protectedHandles.enable = true;
      systemdCredentials.enable = true;
      executionIsolation.enable = true;
    };
  };
}
