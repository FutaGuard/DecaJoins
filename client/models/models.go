// Package models defines the shared data types exchanged with the host API.
package models

import "time"

// ── Node ─────────────────────────────────────────────────────────────────────

type NodeStatus string

const (
	NodeStatusOnline  NodeStatus = "online"
	NodeStatusOffline NodeStatus = "offline"
)

// NodeInfo mirrors the host's NodeInfo model.
type NodeInfo struct {
	Name          string     `json:"name"`
	IP            string     `json:"ip"`
	Status        NodeStatus `json:"status"`
	LastHeartbeat time.Time  `json:"last_heartbeat"`
}

// ── Task ─────────────────────────────────────────────────────────────────────

// JoinTarget is the payload a node must act on.
type JoinTarget struct {
	InviteLink string `json:"invite_link"`
	WaitMin    int    `json:"wait_min"`
	WaitMax    int    `json:"wait_max"`
}

// PendingTask is the structure returned by GET /api/tasks/pending.
type PendingTask struct {
	ID      string     `json:"id"`
	Target  JoinTarget `json:"target"`
	Retries int        `json:"retries"`
}

// ── API I/O ──────────────────────────────────────────────────────────────────

// RegisterRequest is sent to POST /api/nodes/register.
type RegisterRequest struct {
	Name string `json:"name"`
	IP   string `json:"ip"`
}

// RegisterResponse is returned from POST /api/nodes/register.
type RegisterResponse struct {
	Name string `json:"name"`
}

// StatusResponse is the generic success envelope.
type StatusResponse struct {
	OK      bool   `json:"ok"`
	Message string `json:"message"`
}

// TaskResultRequest is sent to POST /api/tasks/{id}/result.
type TaskResultRequest struct {
	Success   bool        `json:"success"`
	Result    interface{} `json:"result,omitempty"`
	Error     *string     `json:"error,omitempty"`
	ElapsedMs *int64      `json:"elapsed_ms,omitempty"`
	Retries   int         `json:"retries"`
}
