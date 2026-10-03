# Illustrative OmnisOS configuration. Exact option paths may evolve until the OmnisOS module schema
# is implemented; the architectural split is normative.
{ config, pkgs, ... }:
{
  omnis = {
    graph = {
      enable = true;
      storage = "/var/lib/omnis/graph.db";
    };

    manager = {
      enable = true;
      discovery.enable = true;

      harnesses = {
        claude.enable = true;
        codex.enable = true;
        opencode.enable = true;
      };

      inference.local.enable = true;
    };

    agent = {
      enable = true;
      worldline.storage = "/var/lib/omnis/agent";
      memory.enable = true;
      inferenceInterception.enable = true;
    };

    control = {
      enable = true;
      defaultMode = "2d"; # "2d" or "3d"; same graph/selection/focus state
      shell = pkgs.zsh;
      xwayland.enable = true;
    };

    security = {
      protectedHandles.enable = true;
      executionIsolation.enable = true;
    };
  };
}
