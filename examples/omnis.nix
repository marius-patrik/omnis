# OmnisOS v0 reference configuration.
{ pkgs, ... }:
{
  omnis = {
    enable = true;

    graph = {
      enable = true;
      dataDir = "/var/lib/omnis/graph";
      socket = "/run/omnis/graph.sock";
      writerQueue = 4096;
      query = {
        defaultLimit = 1000;
        hardLimit = 10000;
        maxDepth = 8;
      };
    };

    os = {
      enable = true;
      observe = {
        systemd = true;
        udev = true;
        rtnetlink = true;
        processes = true;
        sessions = true;
        cgroups = true;
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
      };
    };

    agentAccess = {
      enable = true;
      mcp.enable = true;
      pluginSdk.enable = true;
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
      defaultExecutionNetwork = "deny";
    };
  };
}
