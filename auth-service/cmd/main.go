package main

import (
	"fmt"
	"log"

	"github.com/ecommerce/auth-service/internal/handlers"
)

func main() {
	handler := handlers.NewAuthHandler("super-secret-key")

	user, err := handler.Register("john@example.com", "SecurePass123", "John Doe")
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("User registered: %s\n", user.Email)

	token, err := handler.Login("john@example.com", "SecurePass123")
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Login successful! Token: %s\n", token[:20]+"...")

	claims, err := handler.ValidateToken(token)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Token validated for user: %s\n", (*claims)["email"])
}
