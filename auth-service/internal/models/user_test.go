package models

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestValidateEmail(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name  string
		email string
		valid bool
	}{
		{"valid simple", "user@example.com", true},
		{"valid subdomain", "name.surname+tag@sub.example.co", true},
		{"valid numbers", "user123@domain.io", true},
		{"empty", "", false},
		{"no at", "plainaddress", false},
		{"missing domain", "user@", false},
		{"missing user", "@domain.com", false},
		{"one-letter TLD", "user@domain.c", false},
		{"double at", "user@@domain.com", false},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			assert.Equal(t, tt.valid, ValidateEmail(tt.email))
		})
	}
}

func TestValidatePassword(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name     string
		password string
		wantErr  bool
		errMsg   string
	}{
		{"too short", "Abc12", true, "password must be at least 8 characters long"},
		{"no uppercase", "alllowercase1", true, "password must contain uppercase, lowercase, and numeric characters"},
		{"no lowercase", "ALLUPPERCASE1", true, "password must contain uppercase, lowercase, and numeric characters"},
		{"no number", "MixedCaseNoNumber", true, "password must contain uppercase, lowercase, and numeric characters"},
		{"valid min length", "Abcdef1G", false, ""},
		{"valid longer", "StrongPass1", false, ""},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			err := ValidatePassword(tt.password)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Equal(t, tt.errMsg, err.Error())
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestHashPasswordAndCheck(t *testing.T) {
	t.Parallel()
	pw := "StrongPass1"
	hash, err := HashPassword(pw)
	assert.NoError(t, err)
	assert.NotEmpty(t, hash)
	assert.NotEqual(t, pw, hash)

	assert.True(t, CheckPasswordHash(pw, hash))
	assert.False(t, CheckPasswordHash("WrongPassword1", hash))
}

func TestNewUser_Success(t *testing.T) {
	t.Parallel()
	email := "john.doe@example.com"
	name := "John Doe"
	pw := "GoodPass1"

	user, err := NewUser(email, pw, name)
	assert.NoError(t, err)
	assert.NotNil(t, user)

	assert.Equal(t, email, user.Email)
	assert.Equal(t, name, user.Name)
	assert.NotEmpty(t, user.Password)
	assert.NotEqual(t, pw, user.Password)
	assert.True(t, CheckPasswordHash(pw, user.Password))

	now := time.Now()
	assert.WithinDuration(t, now, user.CreatedAt, 2*time.Second)
	assert.WithinDuration(t, now, user.LastActivity, 2*time.Second)
	assert.Equal(t, 0, user.LoginCount)
}

func TestNewUser_InvalidEmail(t *testing.T) {
	t.Parallel()
	user, err := NewUser("invalid-email", "Abcdefg1", "Name")
	assert.Nil(t, user)
	assert.Error(t, err)
	assert.Equal(t, "invalid email format", err.Error())
}

func TestNewUser_InvalidPassword(t *testing.T) {
	t.Parallel()
	user, err := NewUser("user@example.com", "short", "Name")
	assert.Nil(t, user)
	assert.Error(t, err)
	assert.Equal(t, "password must be at least 8 characters long", err.Error())
}

func TestUser_RecordActivity(t *testing.T) {
	t.Parallel()
	u := &User{
		Email:        "u@example.com",
		Password:     "hash",
		Name:         "U",
		CreatedAt:    time.Now().Add(-24 * time.Hour),
		LastActivity: time.Now().Add(-48 * time.Hour),
		LoginCount:   0,
	}

	before := u.LastActivity
	u.RecordActivity()
	assert.True(t, u.LastActivity.After(before), "LastActivity should be updated to a later time")
	assert.WithinDuration(t, time.Now(), u.LastActivity, 2*time.Second)
}

func TestUser_IncrementLoginCount(t *testing.T) {
	t.Parallel()
	u := &User{
		Email:        "u@example.com",
		Password:     "hash",
		Name:         "U",
		CreatedAt:    time.Now().Add(-24 * time.Hour),
		LastActivity: time.Now().Add(-24 * time.Hour),
		LoginCount:   3,
	}

	beforeAct := u.LastActivity
	u.IncrementLoginCount()
	assert.Equal(t, 4, u.LoginCount)
	assert.True(t, u.LastActivity.After(beforeAct))
	assert.WithinDuration(t, time.Now(), u.LastActivity, 2*time.Second)
}

func TestUser_IsActive(t *testing.T) {
	t.Parallel()
	now := time.Now()

	u := &User{
		Email:        "u@example.com",
		Password:     "hash",
		Name:         "U",
		CreatedAt:    now.Add(-60 * 24 * time.Hour),
		LastActivity: now.Add(-5 * 24 * time.Hour),
		LoginCount:   0,
	}

	// Non-positive window always true
	assert.True(t, u.IsActive(0))
	assert.True(t, u.IsActive(-10))

	// Within 7 days
	assert.True(t, u.IsActive(7))
	// Within 30 days
	assert.True(t, u.IsActive(30))
	// Not within 3 days
	assert.False(t, u.IsActive(3))

	// 31 days ago
	u.LastActivity = now.Add(-31 * 24 * time.Hour)
	assert.False(t, u.IsActive(30))
	assert.True(t, u.IsActive(60))
}

func TestUser_GetActivityScore_RecentActivityBoost20(t *testing.T) {
	t.Parallel()
	now := time.Now()
	u := &User{
		Email:        "u@example.com",
		Password:     "hash",
		Name:         "U",
		CreatedAt:    now.Add(-10 * 24 * time.Hour),
		LastActivity: now.Add(-3 * 24 * time.Hour), // active within 7
		LoginCount:   5,
	}

	// Compute expected using the same logic to avoid rounding surprises
	daysSinceCreation := int(time.Since(u.CreatedAt).Hours() / 24)
	if daysSinceCreation == 0 {
		daysSinceCreation = 1
	}
	expected := (u.LoginCount * 10) / daysSinceCreation
	if u.IsActive(7) {
		expected += 20
	} else if u.IsActive(30) {
		expected += 10
	}

	assert.Equal(t, expected, u.GetActivityScore())
}

func TestUser_GetActivityScore_ModerateActivityBoost10(t *testing.T) {
	t.Parallel()
	now := time.Now()
	u := &User{
		Email:        "u@example.com",
		Password:     "hash",
		Name:         "U",
		CreatedAt:    now.Add(-40 * 24 * time.Hour),
		LastActivity: now.Add(-10 * 24 * time.Hour), // not active within 7, but within 30
		LoginCount:   3,
	}

	daysSinceCreation := int(time.Since(u.CreatedAt).Hours() / 24)
	if daysSinceCreation == 0 {
		daysSinceCreation = 1
	}
	expected := (u.LoginCount * 10) / daysSinceCreation
	if u.IsActive(7) {
		expected += 20
	} else if u.IsActive(30) {
		expected += 10
	}

	assert.Equal(t, expected, u.GetActivityScore())
}

func TestUser_GetActivityScore_NoBoost(t *testing.T) {
	t.Parallel()
	now := time.Now()
	u := &User{
		Email:        "u@example.com",
		Password:     "hash",
		Name:         "U",
		CreatedAt:    now.Add(-40 * 24 * time.Hour),
		LastActivity: now.Add(-40 * 24 * time.Hour), // inactive >30
		LoginCount:   12,
	}

	daysSinceCreation := int(time.Since(u.CreatedAt).Hours() / 24)
	if daysSinceCreation == 0 {
		daysSinceCreation = 1
	}
	expected := (u.LoginCount * 10) / daysSinceCreation
	if u.IsActive(7) {
		expected += 20
	} else if u.IsActive(30) {
		expected += 10
	}

	assert.Equal(t, expected, u.GetActivityScore())
}

func TestUser_GetActivityScore_DaysSinceCreationZeroHandled(t *testing.T) {
	t.Parallel()
	now := time.Now()
	u := &User{
		Email:        "u@example.com",
		Password:     "hash",
		Name:         "U",
		CreatedAt:    now, // daysSinceCreation will be 0, should be treated as 1
		LastActivity: now, // active within 7
		LoginCount:   3,   // base (3*10)/1 = 30
	}

	daysSinceCreation := int(time.Since(u.CreatedAt).Hours() / 24)
	if daysSinceCreation == 0 {
		daysSinceCreation = 1
	}
	expected := (u.LoginCount * 10) / daysSinceCreation
	if u.IsActive(7) {
		expected += 20
	} else if u.IsActive(30) {
		expected += 10
	}

	assert.Equal(t, expected, u.GetActivityScore())
}
