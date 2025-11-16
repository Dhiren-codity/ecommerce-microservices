package models

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func timeNearNow(t *testing.T, ts time.Time, within time.Duration) {
	t.Helper()
	now := time.Now()
	diff := now.Sub(ts)
	if diff < 0 {
		diff = -diff
	}
	assert.LessOrEqual(t, diff, within, "timestamp %v not within %v of now %v", ts, within, now)
}

func TestValidateEmail(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name  string
		email string
		ok    bool
	}{
		{"simple", "alice@example.com", true},
		{"plus", "bob+tag@sub.domain.io", true},
		{"dots", "first.last@company.co", true},
		{"missing-at", "notanemail", false},
		{"missing-tld", "user@domain", false},
		{"short-tld", "user@domain.c", false},
		{"space", "user @example.com", false},
		{"invalid-char-domain-underscore", "a@b_c.com", false},
		{"invalid-char-local-space", "a b@example.com", false},
	}
	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			got := ValidateEmail(tt.email)
			assert.Equal(t, tt.ok, got)
		})
	}
}

func TestValidatePassword(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name string
		pw   string
		ok   bool
		msg  string
	}{
		{"valid-minimum", "Abcdefg1", true, ""},
		{"valid-with-special", "A!bcdef1g", true, ""},
		{"valid-with-space", "Abcd ef1", true, ""}, // spaces are allowed by current rules
		{"too-short", "Abcdef1", false, "password must be at least 8 characters long"},
		{"no-upper", "abcdefg1", false, "password must contain uppercase, lowercase, and numeric characters"},
		{"no-lower", "ABCDEFG1", false, "password must contain uppercase, lowercase, and numeric characters"},
		{"no-number", "Abcdefgh", false, "password must contain uppercase, lowercase, and numeric characters"},
	}
	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			err := ValidatePassword(tt.pw)
			if tt.ok {
				assert.NoError(t, err)
			} else {
				if assert.Error(t, err) && tt.msg != "" {
					assert.Equal(t, tt.msg, err.Error())
				}
			}
		})
	}
}

func TestHashPassword_And_CheckPasswordHash(t *testing.T) {
	t.Parallel()
	pw := "Abcdefg1"
	hash, err := HashPassword(pw)
	assert.NoError(t, err)
	assert.NotEmpty(t, hash)
	assert.NotEqual(t, pw, hash)

	assert.True(t, CheckPasswordHash(pw, hash))
	assert.False(t, CheckPasswordHash("wrongpass1", hash))
	assert.False(t, CheckPasswordHash(pw, "not-a-valid-bcrypt-hash"))
}

func TestNewUser_Success(t *testing.T) {
	t.Parallel()
	email := "user@example.com"
	pw := "Abcdefg1"
	name := "Test User"

	u, err := NewUser(email, pw, name)
	assert.NoError(t, err)
	if assert.NotNil(t, u) {
		assert.Equal(t, email, u.Email)
		assert.Equal(t, name, u.Name)
		// ID is not set by NewUser in current implementation
		assert.Equal(t, "", u.ID)

		assert.NotEmpty(t, u.Password)
		assert.NotEqual(t, pw, u.Password)
		assert.True(t, CheckPasswordHash(pw, u.Password))

		assert.Equal(t, 0, u.LoginCount)
		timeNearNow(t, u.CreatedAt, 2*time.Second)
		timeNearNow(t, u.LastActivity, 2*time.Second)
		// LastActivity should not be before CreatedAt
		assert.False(t, u.LastActivity.Before(u.CreatedAt))
	}
}

func TestNewUser_InvalidEmail(t *testing.T) {
	t.Parallel()
	u, err := NewUser("invalid-email", "Abcdefg1", "Name")
	assert.Nil(t, u)
	if assert.Error(t, err) {
		assert.Equal(t, "invalid email format", err.Error())
	}
}

func TestNewUser_WeakPassword(t *testing.T) {
	t.Parallel()
	u, err := NewUser("user@example.com", "weak", "Name")
	assert.Nil(t, u)
	if assert.Error(t, err) {
		assert.Equal(t, "password must be at least 8 characters long", err.Error())
	}
}

func TestUser_RecordActivity(t *testing.T) {
	t.Parallel()
	u := &User{
		Email:        "user@example.com",
		Password:     "hash",
		Name:         "User",
		CreatedAt:    time.Now().Add(-24 * time.Hour),
		LastActivity: time.Now().Add(-24 * time.Hour),
		LoginCount:   5,
	}
	old := u.LastActivity
	u.RecordActivity()

	assert.True(t, u.LastActivity.After(old) || u.LastActivity.Equal(old) == false)
	timeNearNow(t, u.LastActivity, 2*time.Second)
	// Ensure other fields remain unchanged
	assert.Equal(t, 5, u.LoginCount)
	assert.Equal(t, "User", u.Name)
}

func TestUser_IncrementLoginCount(t *testing.T) {
	t.Parallel()
	u := &User{
		Email:        "user@example.com",
		Password:     "hash",
		Name:         "User",
		CreatedAt:    time.Now().Add(-48 * time.Hour),
		LastActivity: time.Now().Add(-48 * time.Hour),
		LoginCount:   0,
	}
	oldLA := u.LastActivity
	u.IncrementLoginCount()

	assert.Equal(t, 1, u.LoginCount)
	assert.True(t, u.LastActivity.After(oldLA))
	timeNearNow(t, u.LastActivity, 2*time.Second)
}

func TestUser_IsActive(t *testing.T) {
	t.Parallel()
	now := time.Now()

	t.Run("inactiveDays<=0 always true", func(t *testing.T) {
		u := &User{LastActivity: now.Add(-365 * 24 * time.Hour)}
		assert.True(t, u.IsActive(0))
		assert.True(t, u.IsActive(-5))
	})

	t.Run("after threshold is active", func(t *testing.T) {
		u := &User{LastActivity: time.Now().AddDate(0, 0, -7).Add(1 * time.Second)}
		assert.True(t, u.IsActive(7))
	})

	t.Run("equal to threshold is not active", func(t *testing.T) {
		u := &User{LastActivity: time.Now().AddDate(0, 0, -7)}
		assert.False(t, u.IsActive(7))
	})

	t.Run("before threshold is not active", func(t *testing.T) {
		u := &User{LastActivity: time.Now().AddDate(0, 0, -8)}
		assert.False(t, u.IsActive(7))
	})
}

func TestUser_GetActivityScore(t *testing.T) {
	t.Parallel()

	t.Run("very new and active within 7 days", func(t *testing.T) {
		u := &User{
			CreatedAt:    time.Now(),
			LastActivity: time.Now(),
			LoginCount:   3,
		}
		// daysSinceCreation -> 0 => 1; base = 3*10/1 = 30; +20 active(7) => 50
		assert.Equal(t, 50, u.GetActivityScore())
	})

	t.Run("active within 30 days but not 7", func(t *testing.T) {
		u := &User{
			CreatedAt:    time.Now().AddDate(0, 0, -10),
			LastActivity: time.Now().AddDate(0, 0, -20),
			LoginCount:   5,
		}
		// base = (5*10)/10 = 5; +10 (active within 30 but not 7) => 15
		assert.Equal(t, 15, u.GetActivityScore())
	})

	t.Run("inactive beyond 30 days", func(t *testing.T) {
		u := &User{
			CreatedAt:    time.Now().AddDate(0, 0, -40),
			LastActivity: time.Now().AddDate(0, 0, -40),
			LoginCount:   12,
		}
		// base = (12*10)/40 = 3; +0 => 3
		assert.Equal(t, 3, u.GetActivityScore())
	})

	t.Run("division floors for daysSinceCreation", func(t *testing.T) {
		u := &User{
			CreatedAt:    time.Now().Add(-26 * time.Hour), // 1 day when floored
			LastActivity: time.Now().Add(-8 * 24 * time.Hour),
			LoginCount:   9,
		}
		// daysSinceCreation = 1; base = 90/1 = 90; not active within 7, active within 30 => +10 => 100
		assert.Equal(t, 100, u.GetActivityScore())
	})
}
