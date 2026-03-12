<?php
/**
 * User class — PHP 4/5 style, no type hints, no visibility keywords on some methods
 */
require_once 'db.php';

class User {

    var $id;           // PHP 4 style (should be public/protected/private)
    var $username;
    var $email;
    var $role;
    var $created_at;

    // Constructor PHP 4 style
    function User($id = null) {
        if ($id !== null) {
            $this->load($id);
        }
    }

    function load($id) {
        $id = (int) $id;
        $row = db_fetch_one("SELECT * FROM users WHERE id = $id");
        if ($row) {
            $this->id         = $row['id'];
            $this->username   = $row['username'];
            $this->email      = $row['email'];
            $this->role       = $row['role'];
            $this->created_at = $row['created_at'];
        }
    }

    function save() {
        $username = db_escape($this->username);
        $email    = db_escape($this->email);
        $role     = db_escape($this->role);

        if ($this->id) {
            db_execute("UPDATE users SET username='$username', email='$email', role='$role' WHERE id={$this->id}");
        } else {
            db_execute("INSERT INTO users (username, email, role, created_at) VALUES ('$username','$email','$role', NOW())");
            $this->id = db_last_id();
        }
    }

    function delete() {
        db_execute("DELETE FROM users WHERE id={$this->id}");
    }

    // Static finder — old style
    function find_by_email($email) {
        $email = db_escape($email);
        return db_fetch_one("SELECT * FROM users WHERE email='$email' LIMIT 1");
    }

    function find_all() {
        return db_fetch_all("SELECT * FROM users ORDER BY created_at DESC");
    }

    function is_admin() {
        return $this->role == 'admin';
    }

    // Password hash using old md5 (insecure)
    function set_password($plain) {
        $hash = md5($plain);   // Should use password_hash()
        db_execute("UPDATE users SET password='$hash' WHERE id={$this->id}");
    }

    function check_password($plain, $hash) {
        return md5($plain) == $hash;  // Should use password_verify()
    }
}
