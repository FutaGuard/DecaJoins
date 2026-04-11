// DecaJoins Node Client — connects to a DecaJoins host and executes tasks.
//
// Usage:
//
//	./client [-config path/to/config.yml]
//
// The default config file path is "config.yml" in the working directory.
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"decajoins-client/config"
	"decajoins-client/models"
	clientnode "decajoins-client/node"
)

func main() {
	cfgPath := flag.String("config", "config.yml", "path to YAML config file")
	flag.Parse()

	// ── Load config ──────────────────────────────────────────────────────────
	cfg, err := config.Load(*cfgPath)
	if err != nil {
		slog.Error("failed to load config", "err", err)
		os.Exit(1)
	}

	slog.Info("starting node client",
		"name", cfg.Name,
		"host_url", cfg.HostURL,
		"poll_interval", cfg.PollInterval.Duration,
		"heartbeat_interval", cfg.HeartbeatInterval.Duration,
	)

	// ── Build node config ────────────────────────────────────────────────────
	nodeCfg := clientnode.Config{
		Name:              cfg.Name,
		HostURL:           cfg.HostURL,
		AuthToken:         cfg.AuthToken,
		PollInterval:      cfg.PollInterval.Duration,
		HeartbeatInterval: cfg.HeartbeatInterval.Duration,
	}

	// ── Task handler (business logic) ────────────────────────────────────────
	// Replace / extend this function with your actual join implementation.
	handler := func(ctx context.Context, task models.PendingTask) (interface{}, error) {
		slog.Info("handling task",
			"task_id", task.ID,
			"invite_link", task.Target.InviteLink,
			"wait_min", task.Target.WaitMin,
			"wait_max", task.Target.WaitMax,
		)

		// ── TODO: implement real join logic here ─────────────────────────────
		// Example placeholder: simulate success after a brief pause.
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(500 * time.Millisecond):
		}

		return map[string]interface{}{
			"status": "joined",
			"link":   task.Target.InviteLink,
		}, nil
	}

	// ── Run ──────────────────────────────────────────────────────────────────
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	n := clientnode.New(nodeCfg, handler)
	if err := n.Run(ctx); err != nil && !errors.Is(err, context.Canceled) {
		fmt.Fprintf(os.Stderr, "node exited with error: %v\n", err)
		os.Exit(1)
	}

	slog.Info("node stopped gracefully")
}
