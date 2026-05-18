#!/bin/bash

# ==============================================================================
# AI Selective Chat Sync Script (Method A - Practical Setup)
# ==============================================================================
# This script selectively shares individual Antigravity chats via your OneDrive
# project directory, keeping other personal chats 100% private.
# ==============================================================================

# Set up paths relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SHARED_DIR="$PROJECT_DIR/docs/ai-context/shared-chats"
LOCAL_APP_DIR="$HOME/.gemini/antigravity"

# Create directories if they do not exist
mkdir -p "$SHARED_DIR/conversations"
mkdir -p "$SHARED_DIR/brain"
mkdir -p "$LOCAL_APP_DIR/conversations"
mkdir -p "$LOCAL_APP_DIR/brain"

echo "🎯 Project Directory: $PROJECT_DIR"
echo "📂 Shared OneDrive Folder: $SHARED_DIR"
echo "💻 Local AI App Directory: $LOCAL_APP_DIR"
echo "--------------------------------------------------"

# Function: Sync incoming chats from OneDrive to Local App
sync_incoming() {
    echo "🔍 Scanning for chats shared by your partner in OneDrive..."
    
    # Check if there are any shared conversations
    shopt -s nullglob
    shared_files=("$SHARED_DIR/conversations"/*.pb)
    
    if [ ${#shared_files[@]} -eq 0 ]; then
        echo "ℹ️  No shared chats found in the OneDrive folder yet."
        return 0
    fi
    
    for shared_path in "${shared_files[@]}"; do
        filename=$(basename "$shared_path")
        chat_id="${filename%.pb}"
        
        echo "   Found shared chat ID: $chat_id"
        
        # 1. Symlink the conversation file
        local_conv_path="$LOCAL_APP_DIR/conversations/$filename"
        if [ ! -L "$local_conv_path" ]; then
            # Clean up local file if it somehow exists and is not a symlink
            if [ -f "$local_conv_path" ]; then
                mv "$local_conv_path" "${local_conv_path}.bak"
                echo "   ⚠️ Backed up pre-existing local chat file to .bak"
            fi
            ln -s "$shared_path" "$local_conv_path"
            echo "   ✅ Symlinked conversation file to local app."
        else
            echo "   ✓ Conversation file already symlinked."
        fi
        
        # 2. Symlink the brain folder
        local_brain_path="$LOCAL_APP_DIR/brain/$chat_id"
        shared_brain_path="$SHARED_DIR/brain/$chat_id"
        
        # Ensure shared brain folder exists
        mkdir -p "$shared_brain_path"
        
        if [ ! -L "$local_brain_path" ]; then
            # Clean up local directory if it exists and is not a symlink
            if [ -d "$local_brain_path" ]; then
                mv "$local_brain_path" "${local_brain_path}_bak"
                echo "   ⚠️ Backed up pre-existing local brain folder to _bak"
            fi
            ln -s "$shared_brain_path" "$local_brain_path"
            echo "   ✅ Symlinked brain context directory."
        else
            echo "   ✓ Brain context already symlinked."
        fi
    done
    echo "🎉 Sync complete! All shared chats are now available in your sidebar history."
}

# Function: Share a local chat by ID
share_chat_id() {
    local chat_id="$1"
    
    # Check if this chat ID actually exists locally
    local_pb="$LOCAL_APP_DIR/conversations/${chat_id}.pb"
    local_brain="$LOCAL_APP_DIR/brain/${chat_id}"
    
    if [ ! -f "$local_pb" ]; then
        echo "❌ Error: Conversation ID '$chat_id' not found in your local history ($local_pb)."
        exit 1
    fi
    
    echo "📤 Sharing chat ID: $chat_id"
    
    # 1. Handle conversation file
    shared_pb="$SHARED_DIR/conversations/${chat_id}.pb"
    if [ ! -f "$shared_pb" ] && [ ! -L "$local_pb" ]; then
        mv "$local_pb" "$shared_pb"
        ln -s "$shared_pb" "$local_pb"
        echo "   ✅ Moved and symlinked conversation file."
    elif [ -L "$local_pb" ]; then
        echo "   ✓ Conversation file is already shared/symlinked."
    fi
    
    # 2. Handle brain directory
    shared_brain="$SHARED_DIR/brain/${chat_id}"
    mkdir -p "$shared_brain"
    
    if [ -d "$local_brain" ] && [ ! -L "$local_brain" ]; then
        # Move files inside local brain to shared brain
        cp -R "$local_brain"/* "$shared_brain/" 2>/dev/null
        rm -rf "$local_brain"
        ln -s "$shared_brain" "$local_brain"
        echo "   ✅ Moved and symlinked brain context."
    elif [ ! -e "$local_brain" ]; then
        ln -s "$shared_brain" "$local_brain"
        echo "   ✅ Created symlink for new empty brain context."
    elif [ -L "$local_brain" ]; then
        echo "   ✓ Brain context is already shared/symlinked."
    fi
    
    echo "🎉 Successfully shared! It is now synced to OneDrive. Once your partner runs this script, they will see it."
}

# Function: Auto-detect the most recent local chat
detect_latest_chat() {
    echo "🔍 Scanning for your most recently active local chat..."
    
    # Find the most recently modified .pb file that is NOT a symlink
    latest_pb=""
    latest_time=0
    
    for f in "$LOCAL_APP_DIR/conversations"/*.pb; do
        if [ -f "$f" ] && [ ! -L "$f" ]; then
            mtime=$(stat -f "%m" "$f" 2>/dev/null || stat -c "%Y" "$f")
            if [ "$mtime" -gt "$latest_time" ]; then
                latest_time=$mtime
                latest_pb=$f
            fi
        fi
    done
    
    if [ -n "$latest_pb" ]; then
        chat_id=$(basename "$latest_pb" .pb)
        echo "💡 Detected latest local chat: $chat_id"
        
        # Read the first user prompt from logs if available to give a preview
        log_file="$LOCAL_APP_DIR/brain/$chat_id/.system_generated/logs/overview.txt"
        if [ -f "$log_file" ]; then
            preview=$(grep -m 1 -o '"content":"[^"]*' "$log_file" | head -n 1 | sed 's/"content":"//' | cut -c 1-60)
            echo "   Preview: \"$preview...\""
        fi
        
        read -p "❓ Do you want to share this chat with your partner? (y/n): " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            share_chat_id "$chat_id"
        else
            echo "❌ Canceled."
        fi
    else
        echo "ℹ️  No unshared local chats detected."
    fi
}

# Function: Automatically install Git hooks for background automation
install_git_hooks() {
    local hooks_dir="$PROJECT_DIR/.git/hooks"
    if [ -d "$hooks_dir" ]; then
        # 1. post-merge hook (runs after git pull/merge)
        post_merge_hook="$hooks_dir/post-merge"
        cat << 'EOF' > "$post_merge_hook"
#!/bin/bash
# Automatically sync shared chats after a git pull / merge
echo "🔄 Git post-merge: Syncing incoming AI chats from OneDrive..."
"./docs/ai-context/share-chat.sh" --sync 2>/dev/null
EOF
        chmod +x "$post_merge_hook"

        # 2. pre-push hook (runs before git push)
        pre_push_hook="$hooks_dir/pre-push"
        cat << 'EOF' > "$pre_push_hook"
#!/bin/bash
# Automatically detect and share the latest active chat before pushing code
LOCAL_APP_DIR="$HOME/.gemini/antigravity"
latest_pb=""
latest_time=0

for f in "$LOCAL_APP_DIR/conversations"/*.pb; do
    if [ -f "$f" ] && [ ! -L "$f" ]; then
        mtime=$(stat -f "%m" "$f" 2>/dev/null || stat -c "%Y" "$f")
        if [ "$mtime" -gt "$latest_time" ]; then
            latest_time=$mtime
            latest_pb=$f
        fi
    fi
done

if [ -n "$latest_pb" ]; then
    chat_id=$(basename "$latest_pb" .pb)
    echo "🔄 Git pre-push: Automatically sharing latest active AI chat ($chat_id)..."
    "./docs/ai-context/share-chat.sh" "$chat_id" >/dev/null 2>&1
fi
EOF
        chmod +x "$pre_push_hook"
        echo "🔧 Git hooks installed/updated successfully (post-merge & pre-push)!"
    fi
}

# Main routing logic
if [ "$1" == "--sync" ] || [ -z "$1" ]; then
    # Default behavior: Sync any incoming shared chats first
    sync_incoming
    
    # Automatically install/update local hooks
    install_git_hooks
    
    # If explicitly syncing, stop here
    if [ "$1" == "--sync" ]; then
        exit 0
    fi
    
    echo "--------------------------------------------------"
    # Then ask if they want to share their latest local chat
    detect_latest_chat
elif [ -n "$1" ]; then
    # Share a specific chat ID passed as argument
    share_chat_id "$1"
    install_git_hooks
fi
