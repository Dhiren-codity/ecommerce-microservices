package models

import (
	"errors"
	"regexp"
	"time"

	"golang.org/x/crypto/bcrypt"
)

type User struct {
	ID           string    `json:"id"`
	Email        string    `json:"email"`
	Password     string    `json:"-"`
	Name         string    `json:"name"`
	CreatedAt    time.Time `json:"created_at"`
	LastActivity time.Time `json:"last_activity"`
	LoginCount   int       `json:"login_count"`
}

func ValidateEmail(email string) bool {
	emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	return emailRegex.MatchString(email)
}

func ValidatePassword(password string) error {
	if len(password) < 8 {
		return errors.New("password must be at least 8 characters long")
	}

	hasUpper := regexp.MustCompile(`[A-Z]`).MatchString(password)
	hasLower := regexp.MustCompile(`[a-z]`).MatchString(password)
	hasNumber := regexp.MustCompile(`[0-9]`).MatchString(password)

	if !hasUpper || !hasLower || !hasNumber {
		return errors.New("password must contain uppercase, lowercase, and numeric characters")
	}

	return nil
}

func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

func CheckPasswordHash(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

func NewUser(email, password, name string) (*User, error) {
	if !ValidateEmail(email) {
		return nil, errors.New("invalid email format")
	}

	if err := ValidatePassword(password); err != nil {
		return nil, err
	}

	hashedPassword, err := HashPassword(password)
	if err != nil {
		return nil, err
	}

	return &User{
		Email:        email,
		Password:     hashedPassword,
		Name:         name,
		CreatedAt:    time.Now(),
		LastActivity: time.Now(),
		LoginCount:   0,
	}, nil
}

func (u *User) RecordActivity() {
	u.LastActivity = time.Now()
}

func (u *User) IncrementLoginCount() {
	u.LoginCount++
	u.LastActivity = time.Now()
}

func (u *User) IsActive(inactiveDays int) bool {
	if inactiveDays <= 0 {
		return true
	}
	threshold := time.Now().AddDate(0, 0, -inactiveDays)
	return u.LastActivity.After(threshold)
}

func (u *User) GetActivityScore() int {
	daysSinceCreation := int(time.Since(u.CreatedAt).Hours() / 24)
	if daysSinceCreation == 0 {
		daysSinceCreation = 1
	}

	activityScore := (u.LoginCount * 10) / daysSinceCreation

	if u.IsActive(7) {
		activityScore += 20
	} else if u.IsActive(30) {
		activityScore += 10
	}

	return activityScore
}
