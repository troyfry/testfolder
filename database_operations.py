import sqlite3
from typing import List, Tuple, Dict
import streamlit as st
import uuid
import json
import os


class DatabaseOperations:
    def __init__(self, db_name: str = "memory_palace.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        self.session_id = st.session_state.session_id

    def create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS palaces (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            name TEXT,
            display_name TEXT,
            UNIQUE(session_id, name)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            palace_id INTEGER,
            item_name TEXT,
            FOREIGN KEY (palace_id) REFERENCES palaces (id)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            name TEXT,
            UNIQUE(session_id, name)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS associations (
            id INTEGER PRIMARY KEY,
            topic TEXT,
            category_id INTEGER,
            palace_id INTEGER,
            content TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (palace_id) REFERENCES palaces (id)
        )
        ''')

        self.conn.commit()

    def add_palace(self, name: str) -> int:
        try:
            display_name = name
            namespaced_name = f"{self.session_id}_{name}"
            self.cursor.execute("INSERT INTO palaces (session_id, name, display_name) VALUES (?, ?, ?)",
                                (self.session_id, namespaced_name, display_name))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def add_items(self, palace_id: int, items: List[str]):
        for item in items:
            self.cursor.execute("INSERT INTO items (palace_id, item_name) VALUES (?, ?)", (palace_id, item))
        self.conn.commit()

    def get_palaces(self) -> List[Tuple[int, str]]:
        self.cursor.execute("SELECT id, display_name FROM palaces WHERE session_id = ?", (self.session_id,))
        return self.cursor.fetchall()

    def get_palace_items(self, palace_id: int) -> List[str]:
        self.cursor.execute("SELECT item_name FROM items WHERE palace_id = ?", (palace_id,))
        return [item[0] for item in self.cursor.fetchall()]

    def add_category(self, name: str) -> int:
        try:
            namespaced_name = f"{self.session_id}_{name}"
            self.cursor.execute("INSERT INTO categories (session_id, name) VALUES (?, ?)",
                                (self.session_id, namespaced_name))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_categories(self) -> List[Tuple[int, str]]:
        self.cursor.execute("SELECT id, name FROM categories WHERE session_id = ?", (self.session_id,))
        categories = self.cursor.fetchall()
        # Remove the session_id prefix from the category names before returning
        return [(cat_id, name.split('_', 1)[1]) for cat_id, name in categories]

    def save_association(self, topic: str, category_id: int, palace_id: int, content: str) -> int:
        self.cursor.execute("""
        INSERT INTO associations (topic, category_id, palace_id, content)
        VALUES (?, ?, ?, ?)
        """, (topic, category_id, palace_id, content))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_associations(self, category_id: int) -> List[Tuple[int, str, int, str]]:
        self.cursor.execute("""
        SELECT id, topic, palace_id, content
        FROM associations
        WHERE category_id = ?
        """, (category_id,))
        return self.cursor.fetchall()

    def export_data(self) -> Dict:
        """Export all data for the current session."""
        palaces = self.get_palaces()
        categories = self.get_categories()

        data = {
            "palaces": [],
            "categories": [],
            "associations": []
        }

        for palace_id, palace_name in palaces:
            items = self.get_palace_items(palace_id)
            data["palaces"].append({
                "name": palace_name,
                "items": items
            })

        for category_id, category_name in categories:
            associations = self.get_associations(category_id)
            data["categories"].append({
                "name": category_name,
                "associations": [{
                    "topic": assoc[1],
                    "palace_name": next(
                        p["name"] for p in data["palaces"] if p["name"] == self.get_palace_name(assoc[2])),
                    "content": assoc[3]
                } for assoc in associations]
            })

        return data

    def import_data(self, data: Dict):
        """Import data into the database."""
        for palace in data["palaces"]:
            palace_id = self.add_palace(palace["name"])
            if palace_id:
                self.add_items(palace_id, palace["items"])

        for category in data["categories"]:
            category_id = self.add_category(category["name"])
            if category_id:
                for assoc in category["associations"]:
                    palace_id = self.get_palace_id(assoc["palace_name"])
                    if palace_id:
                        self.save_association(assoc["topic"], category_id, palace_id, assoc["content"])

    def get_palace_name(self, palace_id: int) -> str:
        self.cursor.execute("SELECT display_name FROM palaces WHERE id = ?", (palace_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_palace_id(self, palace_name: str) -> int:
        self.cursor.execute("SELECT id FROM palaces WHERE display_name = ? AND session_id = ?",
                            (palace_name, self.session_id))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def close(self):
        self.conn.close()