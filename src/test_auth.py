import unittest
from unittest.mock import MagicMock
from auth import login, logout

class TestLoginFunction(unittest.TestCase):
    def test_login_default_admin(self):
        result, is_admin = login("admin", "admin123")  # Cambia aquí si tu auth.py usa "admin123"
        self.assertTrue(result)
        self.assertTrue(is_admin)

    def test_login_default_user(self):
        result, is_admin = login("user", "user123")    # Cambia aquí si tu auth.py usa "user123"
        self.assertTrue(result)
        self.assertFalse(is_admin)

    def test_login_default_wrong(self):
        result, is_admin = login("admin", "wrongpass")
        self.assertFalse(result)
        self.assertFalse(is_admin)

    def test_login_with_db_admin(self):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"is_admin": 1}  # Cambiado a dict
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        result, is_admin = login("otro_admin", "otra_clave", conn=mock_conn)
        self.assertTrue(result)
        self.assertTrue(is_admin)
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_login_with_db_user(self):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"is_admin": 0}  # Cambiado a dict
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        result, is_admin = login("otro_user", "otra_clave", conn=mock_conn)
        self.assertTrue(result)
        self.assertFalse(is_admin)
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_login_with_db_not_found(self):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        result, is_admin = login("nouser", "nopass", conn=mock_conn)
        self.assertFalse(result)
        self.assertFalse(is_admin)
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_logout(self):
        try:
            logout()
        except Exception as e:
            self.fail(f"logout() raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()