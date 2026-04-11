// Package api provides a thin HTTP client for the DecaJoins host API.
package api

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"decajoins-client/models"
)

// Client is a reusable HTTP client for the host API.
type Client struct {
	baseURL    string
	authToken  string
	nodeName   string
	httpClient *http.Client
}

// New creates a new Client.
//   - baseURL   e.g. "http://127.0.0.1:8000"
//   - authToken Bearer token configured on the host
//   - nodeName  this node's registered name (used in X-Node-Name header)
func New(baseURL, authToken, nodeName string) *Client {
	return &Client{
		baseURL:   baseURL,
		authToken: authToken,
		nodeName:  nodeName,
		httpClient: &http.Client{
			Timeout: 15 * time.Second,
		},
	}
}

// ── helpers ──────────────────────────────────────────────────────────────────

func (c *Client) newRequest(ctx context.Context, method, path string, body interface{}) (*http.Request, error) {
	var buf io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("marshal body: %w", err)
		}
		buf = bytes.NewReader(b)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, buf)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.authToken)
	req.Header.Set("X-Node-Name", c.nodeName)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	return req, nil
}

func (c *Client) do(req *http.Request, out interface{}) error {
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()

	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("host returned %d: %s", resp.StatusCode, string(raw))
	}
	if out != nil {
		if err := json.Unmarshal(raw, out); err != nil {
			return fmt.Errorf("unmarshal response: %w", err)
		}
	}
	return nil
}

// ── API calls ────────────────────────────────────────────────────────────────

// Register registers (or re-registers) this node with the host.
func (c *Client) Register(ctx context.Context, ip string) (*models.RegisterResponse, error) {
	req, err := c.newRequest(ctx, http.MethodPost, "/api/nodes/register", models.RegisterRequest{
		Name: c.nodeName,
		IP:   ip,
	})
	if err != nil {
		return nil, err
	}
	var resp models.RegisterResponse
	return &resp, c.do(req, &resp)
}

// Heartbeat sends a heartbeat for this node.
// If the host returns 404 the node is no longer registered; the caller should
// re-register.
func (c *Client) Heartbeat(ctx context.Context) error {
	req, err := c.newRequest(ctx, http.MethodPost, "/api/nodes/heartbeat", nil)
	if err != nil {
		return err
	}
	return c.do(req, nil)
}

// GetPendingTasks fetches tasks assigned to this node that have not yet been
// answered.
func (c *Client) GetPendingTasks(ctx context.Context) ([]models.PendingTask, error) {
	req, err := c.newRequest(ctx, http.MethodGet, "/api/tasks/pending", nil)
	if err != nil {
		return nil, err
	}
	var tasks []models.PendingTask
	return tasks, c.do(req, &tasks)
}

// SubmitResult reports the outcome of a task back to the host.
func (c *Client) SubmitResult(ctx context.Context, taskID string, result models.TaskResultRequest) error {
	req, err := c.newRequest(ctx, http.MethodPost, "/api/tasks/"+taskID+"/result", result)
	if err != nil {
		return err
	}
	return c.do(req, nil)
}

// ListNodes returns all nodes known to the host (useful for diagnostics).
func (c *Client) ListNodes(ctx context.Context) ([]models.NodeInfo, error) {
	req, err := c.newRequest(ctx, http.MethodGet, "/api/nodes", nil)
	if err != nil {
		return nil, err
	}
	var nodes []models.NodeInfo
	return nodes, c.do(req, &nodes)
}
