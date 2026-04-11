// Package config loads node client configuration from a YAML file.
package config

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// Config is the top-level configuration structure for the Go client node.
type Config struct {
	// Name is the unique node identifier registered with the host.
	Name string `yaml:"name"`
	// IP overrides the auto-detected outbound IP sent during registration.
	// Leave empty to use auto-detection.
	IP string `yaml:"ip,omitempty"`
	// HostURL is the base URL of the host API, e.g. "http://127.0.0.1:8080".
	HostURL string `yaml:"host_url"`
	// AuthToken is the Bearer token matching the host's auth_token setting.
	AuthToken string `yaml:"auth_token"`
	// PollInterval controls how often pending tasks are fetched (default: 5s).
	PollInterval Duration `yaml:"poll_interval,omitempty"`
	// HeartbeatInterval controls how often heartbeats are sent (default: 20s).
	HeartbeatInterval Duration `yaml:"heartbeat_interval,omitempty"`
}

// Duration is a time.Duration that can be unmarshalled from a YAML string
// such as "5s" or "1m30s".
type Duration struct {
	time.Duration
}

func (d *Duration) UnmarshalYAML(value *yaml.Node) error {
	dur, err := time.ParseDuration(value.Value)
	if err != nil {
		return fmt.Errorf("invalid duration %q: %w", value.Value, err)
	}
	d.Duration = dur
	return nil
}

// Load reads configuration from the given YAML file path.
func Load(path string) (*Config, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open config %q: %w", path, err)
	}
	defer f.Close()

	var cfg Config
	dec := yaml.NewDecoder(f)
	dec.KnownFields(true)
	if err := dec.Decode(&cfg); err != nil {
		return nil, fmt.Errorf("decode config: %w", err)
	}
	if cfg.Name == "" {
		return nil, fmt.Errorf("config: name is required")
	}
	if cfg.HostURL == "" {
		return nil, fmt.Errorf("config: host_url is required")
	}
	if cfg.AuthToken == "" {
		return nil, fmt.Errorf("config: auth_token is required")
	}
	return &cfg, nil
}
