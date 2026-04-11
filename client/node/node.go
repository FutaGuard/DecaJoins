// Package node implements the client-side node lifecycle:
//   - register with the host on startup
//   - send periodic heartbeats (re-registers automatically on 404)
//   - poll for pending tasks and execute them concurrently
package node

import (
	"context"
	"fmt"
	"log/slog"
	"math/rand"
	"net"
	"time"

	"decajoins-client/api"
	"decajoins-client/models"
)

// TaskHandler is the function signature for business-logic task execution.
// Implementations should:
//   - perform the join action described by target
//   - return (result, error)  — result is stored as-is on the host
type TaskHandler func(ctx context.Context, task models.PendingTask) (interface{}, error)

// Config holds per-node runtime settings.
type Config struct {
	// Name is the unique node identifier sent to the host.
	Name string
	// HostURL is the base URL of the host API, e.g. "http://127.0.0.1:8000".
	HostURL string
	// AuthToken is the Bearer token for host API authentication.
	AuthToken string
	// PollInterval is how often the node polls for pending tasks (default 5 s).
	PollInterval time.Duration
	// HeartbeatInterval is how often the node sends heartbeats (default 20 s).
	HeartbeatInterval time.Duration
}

func (c *Config) defaults() {
	if c.PollInterval == 0 {
		c.PollInterval = 5 * time.Second
	}
	if c.HeartbeatInterval == 0 {
		c.HeartbeatInterval = 20 * time.Second
	}
}

// Node manages a single client node's connection to the host.
type Node struct {
	cfg     Config
	client  *api.Client
	handler TaskHandler
	log     *slog.Logger
}

// New creates a Node.  handler is called for every pending task the host
// returns; it runs in its own goroutine.
func New(cfg Config, handler TaskHandler) *Node {
	cfg.defaults()
	return &Node{
		cfg:     cfg,
		client:  api.New(cfg.HostURL, cfg.AuthToken, cfg.Name),
		handler: handler,
		log:     slog.With("node", cfg.Name),
	}
}

// Run starts the node's main loop and blocks until ctx is cancelled.
func (n *Node) Run(ctx context.Context) error {
	ip, err := outboundIP()
	if err != nil {
		n.log.Warn("could not detect outbound IP, using 0.0.0.0", "err", err)
		ip = "0.0.0.0"
	}

	// Initial registration
	if _, err := n.client.Register(ctx, ip); err != nil {
		return fmt.Errorf("initial registration failed: %w", err)
	}
	n.log.Info("registered with host", "ip", ip)

	heartbeatTicker := time.NewTicker(n.cfg.HeartbeatInterval)
	defer heartbeatTicker.Stop()

	pollTicker := time.NewTicker(n.cfg.PollInterval)
	defer pollTicker.Stop()

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()

		case <-heartbeatTicker.C:
			if err := n.client.Heartbeat(ctx); err != nil {
				n.log.Error("heartbeat failed", "err", err)
				// Try to re-register on 404
				if _, regErr := n.client.Register(ctx, ip); regErr != nil {
					n.log.Error("re-registration failed", "err", regErr)
				} else {
					n.log.Info("re-registered after heartbeat failure")
				}
			}

		case <-pollTicker.C:
			tasks, err := n.client.GetPendingTasks(ctx)
			if err != nil {
				n.log.Error("failed to fetch pending tasks", "err", err)
				continue
			}
			if len(tasks) > 0 {
				n.log.Info("received tasks", "count", len(tasks))
				for _, task := range tasks {
					go n.executeTask(ctx, task)
				}
			}
		}
	}
}

// executeTask runs the user-provided handler and submits the result.
func (n *Node) executeTask(ctx context.Context, task models.PendingTask) {
	start := time.Now()
	n.log.Info("executing task", "task_id", task.ID)

	// Add random delay based on target config
	delay := time.Duration(task.Target.WaitMin+rand.Intn(task.Target.WaitMax-task.Target.WaitMin+1)) * time.Second
	time.Sleep(delay)

	result, err := n.handler(ctx, task)
	elapsed := time.Since(start).Milliseconds()

	req := models.TaskResultRequest{
		Success:   err == nil,
		Result:    result,
		Retries:   task.Retries,
		ElapsedMs: &elapsed,
	}
	if err != nil {
		errMsg := err.Error()
		req.Error = &errMsg
	}

	if submitErr := n.client.SubmitResult(ctx, task.ID, req); submitErr != nil {
		n.log.Error("failed to submit result", "task_id", task.ID, "err", submitErr)
		return
	}
	n.log.Info("task completed", "task_id", task.ID, "success", req.Success, "elapsed_ms", elapsed)
}

// outboundIP detects the machine's outbound IP by opening a UDP connection.
func outboundIP() (string, error) {
	conn, err := net.Dial("udp", "8.8.8.8:80")
	if err != nil {
		return "", err
	}
	defer conn.Close()
	localAddr := conn.LocalAddr().(*net.UDPAddr)
	return localAddr.IP.String(), nil
}
