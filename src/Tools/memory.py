

from datetime import datetime
import os
import json


class ConversationMemory:
    def __init__(self, memory_file="conversation_memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
        self.user_sessions = {}  # Maps user_id to current session_id
    
    def _load_memory(self):
        """Load conversation memory from file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_memory(self):
        """Save conversation memory to file."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def get_or_create_session_for_user(self, user_id, current_context_id=None):
        """Get existing session for user or create new one."""
        # Check if user has an active session
        if user_id in self.user_sessions:
            existing_session = self.user_sessions[user_id]
            # Check if session still exists in memory
            if existing_session in self.memory:
                return existing_session
        
        # Create new session or use current context
        if current_context_id:
            session_id = current_context_id
        else:
            # Generate a session ID based on user and timestamp
            session_id = f"{user_id}_{int(datetime.now().timestamp())}"
        
        self.user_sessions[user_id] = session_id
        return session_id
    
    def get_session_memory(self, session_id):
        """Get memory for a specific session."""
        return self.memory.get(session_id, {
            "conversation_history": [],
            "user_preferences": {},
            "past_searches": [],
            "payment_requests": [],
            "created_at": datetime.now().isoformat()
        })
    
    def get_user_conversation_history(self, user_id, limit=5):
        """Get recent conversation history across all sessions for a user."""
        all_conversations = []
        
        for session_id, session_data in self.memory.items():
            if session_id.startswith(user_id) or user_id in session_id:
                for conv in session_data.get("conversation_history", []):
                    all_conversations.append({
                        "session_id": session_id,
                        "timestamp": conv["timestamp"],
                        "user_query": conv["user_query"],
                        "agent_response": conv["agent_response"][:100] + "..." if len(conv["agent_response"]) > 100 else conv["agent_response"]
                    })
        
        # Sort by timestamp and return most recent
        all_conversations.sort(key=lambda x: x["timestamp"], reverse=True)
        return all_conversations[:limit]
    
    def update_session_memory(self, session_id, user_query, agent_response, context=None):
        """Update memory for a session."""
        if session_id not in self.memory:
            self.memory[session_id] = {
                "conversation_history": [],
                "user_preferences": {},
                "past_searches": [],
                "payment_requests": [],
                "created_at": datetime.now().isoformat()
            }
        
        # Add to conversation history
        self.memory[session_id]["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "agent_response": agent_response,
            "context": context
        })
        
        # Keep only last 15 conversations to prevent memory bloat
        if len(self.memory[session_id]["conversation_history"]) > 15:
            self.memory[session_id]["conversation_history"] = \
                self.memory[session_id]["conversation_history"][-15:]
        
        self._save_memory()
    
    def add_user_preference(self, session_id, preference_key, preference_value):
        """Add or update user preference."""
        if session_id not in self.memory:
            self.memory[session_id] = {
                "conversation_history": [],
                "user_preferences": {},
                "past_searches": [],
                "payment_requests": [],
                "created_at": datetime.now().isoformat()
            }
        
        self.memory[session_id]["user_preferences"][preference_key] = preference_value
        self._save_memory()
    
    def add_search_history(self, session_id, search_term, results_count):
        """Add to search history."""
        if session_id not in self.memory:
            self.memory[session_id] = {
                "conversation_history": [],
                "user_preferences": {},
                "past_searches": [],
                "payment_requests": [],
                "created_at": datetime.now().isoformat()
            }
        
        self.memory[session_id]["past_searches"].append({
            "timestamp": datetime.now().isoformat(),
            "search_term": search_term,
            "results_count": results_count
        })
        
        # Keep only last 20 searches
        if len(self.memory[session_id]["past_searches"]) > 20:
            self.memory[session_id]["past_searches"] = \
                self.memory[session_id]["past_searches"][-20:]
        
        self._save_memory()
    
    def add_payment_request(self, session_id, payment_data):
        """Add payment request to memory."""
        if session_id not in self.memory:
            self.memory[session_id] = {
                "conversation_history": [],
                "user_preferences": {},
                "past_searches": [],
                "payment_requests": [],
                "created_at": datetime.now().isoformat()
            }
        
        self.memory[session_id]["payment_requests"].append(payment_data)
        self._save_memory()

# Global memory instance
conversation_memory = ConversationMemory()

