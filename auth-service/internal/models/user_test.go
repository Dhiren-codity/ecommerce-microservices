package models

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestValidateEmail(t *testing.T) {
	tests := []struct {
		email string
		want  bool
	}{
		{"user@example.com", true},
		{"first.last+tag@sub.domain.co", true},
		{"USER@EXAMPLE.ORG", true},
		{"", false},
		{"nope", false},
		{"foo@", false},
		{"@bar.com", false},
		{"user@domain", false},
		{"user@domain..com", false}, // regex will catch
	}

	for _, tt := range tests {
		got := ValidateEmail(tt.email)
		assert.Equalf(t, tt.want, got, "email=%q", tt.email)
	}
}

func TestValidatePassword(t *testing.T) {
	tests := []struct {
		name     string
		password string
		wantErr  string
	}{
		{"valid_minimum", "Abcdefg1", ""},
		{"valid_longer", "StrongPass123", ""},
		{"too_short", "Abc12", "password must be at least 8 characters long"},
		{"missing_upper", "lowercase123", "password must contain uppercase, lowercase, and numeric characters"},
		{"missing_lower", "UPPERCASE123", "password must contain uppercase, lowercase, and numeric characters"},
		{"missing_digit", "NoDigitsHere", "password must contain uppercase, lowercase, and numeric characters"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidatePassword(tt.password)
			if tt.wantErr == "" {
				assert.NoError(t, err)
			} else {
				if assert.Error(t, err) {
					assert.Equal(t, tt.wantErr, err.Error())
				}
			}
		})
	}
}

func TestHashPasswordAndCheckPasswordHash(t *testing.T) {
	raw := "Abcdefg1"
	hash, err := HashPassword(raw)
	assert.NoError(t, err)
	assert.NotEmpty(t, hash)
	assert.NotEqual(t, raw, hash)

	ok := CheckPasswordHash(raw, hash)
	assert.True(t, ok, "expected password to match hash")

	ok = CheckPasswordHash("wrongpass1A", hash)
	assert.False(t, ok, "expected password mismatch to return false")
}

func TestNewUser(t *testing.T) {
	// Success
	start := time.Now()
	u, err := NewUser("user@example.com", "Abcdefg1", "John Doe")
	assert.NoError(t, err)
	if assert.NotNil(t, u) {
		assert.Equal(t, "user@example.com", u.Email)
		assert.Equal(t, "John Doe", u.Name)
		assert.NotEmpty(t, u.Password)
		assert.NotEqual(t, "Abcdefg1", u.Password)
		assert.Equal(t, 0, u.LoginCount)
		// CreatedAt and LastActivity close to now
		assert.WithinDuration(t, time.Now(), u.CreatedAt, 2*time.Second)
		assert.WithinDuration(t, time.Now(), u.LastActivity, 2*time.Second)
		assert.True(t, u.CreatedAt.After(start) || u.CreatedAt.Equal(start))
	}

	// Invalid email
	u, err = NewUser("bad-email", "Abcdefg1", "Name")
	assert.Nil(t, u)
	if assert.Error(t, err) {
		assert.Equal(t, "invalid email format", err.Error())
	}

	// Invalid password (too short)
	u, err = NewUser("user2@example.com", "Abc12", "Name2")
	assert.Nil(t, u)
	if assert.Error(t, err) {
		assert.Equal(t, "password must be at least 8 characters long", err.Error())
	}

	// Invalid password (missing number)
	u, err = NewUser("user3@example.com", "NoDigitsAA", "Name3")
	assert.Nil(t, u)
	if assert.Error(t, err) {
		assert.Equal(t, "password must contain uppercase, lowercase, and numeric characters", err.Error())
	}
}

func TestUser_RecordActivity(t *testing.T) {
	u := &User{
		Email:        "user@example.com",
		Password:     "hashed",
		Name:         "Test",
		CreatedAt:    time.Now().Add(-24 * time.Hour),
		LastActivity: time.Now().Add(-24 * time.Hour),
		LoginCount:   0,
	}
	before := u.LastActivity
	u.RecordActivity()
	assert.True(t, u.LastActivity.After(before) || u.LastActivity.Equal(before))
	assert.WithinDuration(t, time.Now(), u.LastActivity, 2*time.Second)
}

func TestUser_IncrementLoginCount(t *testing.T) {
	u := &User{
		Email:        "user@example.com",
		Password:     "hashed",
		Name:         "Test",
		CreatedAt:    time.Now().Add(-24 * time.Hour),
		LastActivity: time.Now().Add(-24 * time.Hour),
		LoginCount:   3,
	}
	u.IncrementLoginCount()
	assert.Equal(t, 4, u.LoginCount)
	assert.WithinDuration(t, time.Now(), u.LastActivity, 2*time.Second)
}

func TestUser_IsActive(t *testing.T) {
	now := time.Now()

	tests := []struct {
		name         string
		lastActivity time.Time
		inactiveDays int
		want         bool
	}{
		{"inactiveDays_zero_always_true", now.Add(-365 * 24 * time.Hour), 0, true},
		{"inactiveDays_negative_always_true", now.Add(-365 * 24 * time.Hour), -10, true},
		{"within_threshold_7d_true", now.Add(-(6*24*time.Hour + time.Hour)), 7, true},
		{"beyond_threshold_7d_false", now.Add(-(8 * 24 * time.Hour)), 7, false},
		{"within_threshold_30d_true", now.Add(-(15 * 24 * time.Hour)), 30, true},
		{"beyond_threshold_30d_false", now.Add(-(31 * 24 * time.Hour)), 30, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			u := &User{LastActivity: tt.lastActivity}
			got := u.IsActive(tt.inactiveDays)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestUser_GetActivityScore(t *testing.T) {
	now := time.Now()

	tests := []struct {
		name         string
		createdAt    time.Time
		lastActivity time.Time
		loginCount   int
		want         int
	}{
		{
			name:         "active_within_7_days_bonus_20",
			createdAt:    now.Add(-10 * 24 * time.Hour),
			lastActivity: now.Add(-(2 * 24 * time.Hour)),
			loginCount:   5,  // base = (5*10)/10 = 5
			want:         25, // 5 + 20
		},
		{
			name:         "inactive_7_but_active_30_bonus_10",
			createdAt:    now.Add(-20 * 24 * time.Hour),
			lastActivity: now.Add(-(10 * 24 * time.Hour)),
			loginCount:   40, // base = (40*10)/20 = 20
			want:         30, // 20 + 10
		},
		{
			name:         "inactive_over_30_no_bonus",
			createdAt:    now.Add(-60 * 24 * time.Hour),
			lastActivity: now.Add(-(45 * 24 * time.Hour)),
			loginCount:   15, // base = (15*10)/60 = 2
			want:         2,
		},
		{
			name:         "created_today_days_since_creation_floored_to_1",
			createdAt:    now,
			lastActivity: now.Add(-(1 * time.Hour)),
			loginCount:   3,  // base = (3*10)/1 = 30
			want:         50, // 30 + 20
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			u := &User{
				CreatedAt:    tt.createdAt,
				LastActivity: tt.lastActivity,
				LoginCount:   tt.loginCount,
			}
			got := u.GetActivityScore()
			assert.Equal(t, tt.want, got)
		})
	}
}
