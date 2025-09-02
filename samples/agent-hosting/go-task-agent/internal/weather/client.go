package weather

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"
)

// WeatherResponse represents the OpenMeteo API response
type WeatherResponse struct {
	Current struct {
		Temperature float64 `json:"temperature_2m"`
		WindSpeed   float64 `json:"wind_speed_10m"`
	} `json:"current"`
}

// Client handles weather API requests
type Client struct {
	baseURL string
}

// NewClient creates a new weather client
func NewClient() *Client {
	return &Client{
		baseURL: "https://api.open-meteo.com/v1",
	}
}

// GetWeather fetches weather for a city
func (c *Client) GetWeather(input string) (string, error) {
	// Clean the input - remove "User:" prefix and extract actual city name
	cleanInput := c.extractCityFromInput(input)
	
	// Mock weather responses for testing task parsing
	mockWeather := map[string]string{
		"london":    "Today in London it's 15°C with overcast skies and light rain. Wind at 12 km/h from the west.",
		"londra":    "Today in London it's 15°C with overcast skies and light rain. Wind at 12 km/h from the west.",
		"paris":     "Today in Paris it's 18°C with partly cloudy skies. Light breeze at 8 km/h.",  
		"new york":  "Today in New York it's 22°C with sunny skies and wind at 10 mph from the south.",
		"tokyo":     "Today in Tokyo it's 25°C with humid conditions and scattered clouds. Wind at 5 km/h.",
		"rome":      "Today in Rome it's 28°C with bright sunshine. Light wind at 6 km/h from the northwest.",
		"roma":      "Today in Rome it's 28°C with bright sunshine. Light wind at 6 km/h from the northwest.",
	}
	
	// Convert to lowercase for lookup
	cityLower := strings.ToLower(strings.TrimSpace(cleanInput))
	
	if weather, exists := mockWeather[cityLower]; exists {
		return weather, nil
	}
	
	// Default response for unknown cities - use clean city name
	return fmt.Sprintf("Today in %s it's 20°C with partly cloudy skies. Wind at 7 km/h.", cleanInput), nil
}

// extractCityFromInput extracts the actual city name from various input formats
func (c *Client) extractCityFromInput(input string) string {
	cleaned := strings.TrimSpace(input)
	
	// Remove "User:" prefix if present
	if strings.HasPrefix(cleaned, "User:") {
		cleaned = strings.TrimSpace(strings.TrimPrefix(cleaned, "User:"))
	}
	
	// Handle common weather query patterns
	weatherPhrases := []string{
		"weather in ", "tempo a ", "meteo di ", "forecast for ", "weather for ",
		"how is the weather in ", "what's the weather in ", "che tempo fa a ",
	}
	
	lowerCleaned := strings.ToLower(cleaned)
	for _, phrase := range weatherPhrases {
		if strings.Contains(lowerCleaned, phrase) {
			// Extract city after the phrase
			parts := strings.Split(lowerCleaned, phrase)
			if len(parts) > 1 {
				city := strings.TrimSpace(parts[1])
				// Remove common suffixes
				city = strings.TrimSuffix(city, "?")
				city = strings.TrimSuffix(city, ".")
				return city
			}
		}
	}
	
	// If no pattern matches, return the cleaned input
	return cleaned
}

// getCoordinates would normally get lat/lng for a city
func (c *Client) getCoordinates(city string) (float64, float64, error) {
	// Mock coordinates for demo
	return 40.7128, -74.0060, nil // NYC coordinates
}

// callAPI would make the actual API call
func (c *Client) callAPI(lat, lng float64) (*WeatherResponse, error) {
	params := url.Values{}
	params.Add("latitude", fmt.Sprintf("%.4f", lat))
	params.Add("longitude", fmt.Sprintf("%.4f", lng))
	params.Add("current", "temperature_2m,wind_speed_10m")
	
	url := fmt.Sprintf("%s/forecast?%s", c.baseURL, params.Encode())
	
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	var weather WeatherResponse
	if err := json.NewDecoder(resp.Body).Decode(&weather); err != nil {
		return nil, err
	}
	
	return &weather, nil
}