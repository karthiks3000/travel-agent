#!/bin/bash

# load-env.sh - Load environment variables from .env file
# Usage: source ./load-env.sh

# Only set -e if not being sourced (to avoid terminating parent shell)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    set -e
    echo "Error: This script must be sourced, not executed directly."
    echo "Usage: source ./load-env.sh"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default .env file path
ENV_FILE="${1:-.env}"

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to validate environment variable names
validate_var_name() {
    local var_name="$1"
    # Check if variable name is valid (alphanumeric and underscore, not starting with number)
    if [[ "$var_name" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to clean and process variable value
process_var_value() {
    local value="$1"
    
    # Remove surrounding quotes if present
    if [[ "$value" =~ ^\".*\"$ ]] || [[ "$value" =~ ^\'.*\'$ ]]; then
        value="${value:1:-1}"
    fi
    
    echo "$value"
}

# Check for help flag
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: source $0 [ENV_FILE]"
    echo
    echo "Load environment variables from .env file into current shell environment"
    echo
    echo "Arguments:"
    echo "  ENV_FILE    Path to environment file (default: .env)"
    echo
    echo "Environment Variables:"
    echo "  SHOW_LOADED_VARS    Set to 'true' to display loaded variables"
    echo
    echo "Examples:"
    echo "  source $0                    # Load from .env"
    echo "  source $0 .env.development   # Load from specific file"
    echo "  SHOW_LOADED_VARS=true source $0  # Show loaded variables"
    echo
    echo "Note: Must use 'source' to load variables into current shell environment"
    return 0
fi

# Start loading process
print_info "🌍 Travel Agent Environment Loader"
print_info "=================================="
print_info "Loading environment variables from: $ENV_FILE"
echo

# Check if file exists
if [[ ! -f "$ENV_FILE" ]]; then
    print_error "Environment file '$ENV_FILE' not found!"
    return 1
fi

# Check if file is readable
if [[ ! -r "$ENV_FILE" ]]; then
    print_error "Environment file '$ENV_FILE' is not readable!"
    return 1
fi

# Initialize counters
loaded_count=0
skipped_count=0
error_count=0

# Process each line in the .env file - DO THIS AT TOP LEVEL FOR EXPORTS TO WORK
line_number=0
while IFS= read -r line || [[ -n "$line" ]]; do
    ((line_number++))
    
    # Skip empty lines
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*$ ]]; then
        continue
    fi
    
    # Skip comment lines (lines starting with # after optional whitespace)
    if [[ "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Check if line contains an equals sign
    if [[ ! "$line" =~ = ]]; then
        print_warning "Line $line_number: Skipping malformed line (no '=' found): $line"
        ((skipped_count++))
        continue
    fi
    
    # Split the line into key and value
    key="${line%%=*}"
    value="${line#*=}"
    
    # Trim whitespace from key
    key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    # Validate variable name
    if ! validate_var_name "$key"; then
        print_warning "Line $line_number: Invalid variable name '$key', skipping"
        ((skipped_count++))
        continue
    fi
    
    # Process the value (remove quotes, handle special characters)
    value=$(process_var_value "$value")
    
    # Export the variable - THIS HAPPENS AT TOP LEVEL SO IT PERSISTS!
    if export "$key"="$value" 2>/dev/null; then
        print_success "Loaded: $key"
        ((loaded_count++))
    else
        print_error "Line $line_number: Failed to export variable '$key'"
        ((error_count++))
    fi
    
done < "$ENV_FILE"

# Summary
echo
print_info "Summary:"
print_success "$loaded_count variables loaded successfully"

if [[ $skipped_count -gt 0 ]]; then
    print_warning "$skipped_count lines skipped"
fi

if [[ $error_count -gt 0 ]]; then
    print_error "$error_count errors encountered"
fi

# List loaded variables if requested
if [[ "${SHOW_LOADED_VARS:-false}" == "true" ]]; then
    echo
    print_info "Loaded environment variables:"
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and comments
        if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]] || [[ "$line" =~ ^[[:space:]]*$ ]]; then
            continue
        fi
        
        # Extract variable name
        if [[ "$line" =~ = ]]; then
            var_name="${line%%=*}"
            var_name=$(echo "$var_name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            
            if validate_var_name "$var_name"; then
                # Get the variable value
                var_value=$(eval echo "\$${var_name}" 2>/dev/null) || var_value=""
                
                if [[ -n "$var_value" ]]; then
                    # Mask sensitive values (API keys, passwords, tokens)
                    if [[ "$var_name" =~ (API_KEY|PASSWORD|TOKEN|SECRET|PRIVATE) ]]; then
                        masked_value="${var_value:0:8}***"
                        echo "  $var_name=$masked_value"
                    else
                        echo "  $var_name=$var_value"
                    fi
                fi
            fi
        fi
    done < "$ENV_FILE"
fi

# Success message
if [[ $loaded_count -gt 0 ]]; then
    echo
    print_success "Environment variables loaded successfully!"
    print_info "You can now use the loaded variables in your current shell session"
    
    # Show example usage
    echo
    print_info "Example usage:"
    echo "  echo \$NOVA_ACT_API_KEY"
    echo "  echo \$GOOGLE_PLACES_API_KEY"
    echo "  echo \$AWS_PROFILE"
else
    echo
    print_error "No environment variables were loaded!"
    return 1
fi

# Clean up variables used by script (but keep the loaded env vars)
unset ENV_FILE loaded_count skipped_count error_count line_number line key value var_name var_value masked_value
unset -f print_success print_warning print_error print_info validate_var_name process_var_value
