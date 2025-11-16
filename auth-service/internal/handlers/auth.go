package handlers

import (
	"errors"
	"time"

	"github.com/ecommerce/auth-service/internal/models"
	"github.com/golang-jwt/jwt/v5"
)

type AuthHandler struct {
	jwtSecret []byte
	users     map[string]*models.User
}

func NewAuthHandler(secret string) *AuthHandler {
	return &AuthHandler{
		jwtSecret: []byte(secret),
		users:     make(map[string]*models.User),
	}
}

func (h *AuthHandler) Register(email, password, name string) (*models.User, error) {
	if _, exists := h.users[email]; exists {
		return nil, errors.New("user already exists")
	}

	user, err := models.NewUser(email, password, name)
	if err != nil {
		return nil, err
	}

	h.users[email] = user
	return user, nil
}

func (h *AuthHandler) Login(email, password string) (string, error) {
	user, exists := h.users[email]
	if !exists {
		return "", errors.New("user not found")
	}

	if !models.CheckPasswordHash(password, user.Password) {
		return "", errors.New("invalid password")
	}

	token, err := h.GenerateToken(user)
	if err != nil {
		return "", err
	}

	return token, nil
}

func (h *AuthHandler) GenerateToken(user *models.User) (string, error) {
	claims := jwt.MapClaims{
		"user_id": user.ID,
		"email":   user.Email,
		"exp":     time.Now().Add(time.Hour * 24).Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(h.jwtSecret)
}

func (h *AuthHandler) ValidateToken(tokenString string) (*jwt.MapClaims, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("invalid signing method")
		}
		return h.jwtSecret, nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		return &claims, nil
	}

	return nil, errors.New("invalid token")
}

func (h *AuthHandler) GetUser(email string) (*models.User, error) {
	user, exists := h.users[email]
	if !exists {
		return nil, errors.New("user not found")
	}
	return user, nil
}
