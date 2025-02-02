# jos-reinvented-wheel-ui
# Copyright (C) 2025 Jothest2pid 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import sqlite3
from datetime import datetime
from contextlib import contextmanager

DATABASE_NAME = 'chat_database.db'

def init_db():
    with get_db() as db:
        db.execute('''
        CREATE TABLE IF NOT EXISTS saved_chats (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP
        )
        ''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS saved_messages (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES saved_chats(id)
        )
        ''')

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def save_chat(name, messages):
    """Save a chat session with its messages"""
    with get_db() as db:
        # Create new chat entry
        cursor = db.execute(
            'INSERT INTO saved_chats (name, created_at, last_accessed) VALUES (?, ?, ?)',
            (name, datetime.now(), datetime.now())
        )
        chat_id = cursor.lastrowid
        
        # Save all messages
        for msg in messages:
            db.execute(
                'INSERT INTO saved_messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
                (chat_id, msg['role'], msg['content'], datetime.now())
            )
        
        db.commit()
        return chat_id

def get_saved_chats():
    """Get list of all saved chats"""
    with get_db() as db:
        chats = db.execute(
            'SELECT * FROM saved_chats ORDER BY last_accessed DESC'
        ).fetchall()
        return [dict(chat) for chat in chats]

def get_saved_chat(chat_id):
    """Get a specific saved chat and its messages"""
    with get_db() as db:
        chat = db.execute(
            'SELECT * FROM saved_chats WHERE id = ?',
            (chat_id,)
        ).fetchone()
        
        if not chat:
            return None
            
        messages = db.execute(
            'SELECT * FROM saved_messages WHERE chat_id = ? ORDER BY timestamp',
            (chat_id,)
        ).fetchall()
        
        # Update last accessed time
        db.execute(
            'UPDATE saved_chats SET last_accessed = ? WHERE id = ?',
            (datetime.now(), chat_id)
        )
        db.commit()
        
        return {
            'chat': dict(chat),
            'messages': [dict(msg) for msg in messages]
        }

def delete_saved_chat(chat_id):
    """Delete a saved chat and its messages"""
    with get_db() as db:
        db.execute('DELETE FROM saved_messages WHERE chat_id = ?', (chat_id,))
        db.execute('DELETE FROM saved_chats WHERE id = ?', (chat_id,))
        db.commit()

def rename_saved_chat(chat_id, new_name):
    """Rename a saved chat"""
    with get_db() as db:
        db.execute(
            'UPDATE saved_chats SET name = ? WHERE id = ?',
            (new_name, chat_id)
        )
        db.commit()
