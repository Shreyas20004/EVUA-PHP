<?php
/**
 * Authentication — old session-based, no CSRF, SQL injection risks
 */
require_once 'db.php';
require_once 'User.php';

session_start();

/**
 * Log in a user — no prepared statements, MD5 passwords
 */
function auth_login($email, $password) {
    $email    = db_escape($email);
    $row      = db_fetch_one("SELECT * FROM users WHERE email='$email'");

    if (!$row) {
        return false;
    }

    // Insecure MD5 comparison
    if (md5($password) != $row['password']) {
        return false;
    }

    $_SESSION['user_id']   = $row['id'];
    $_SESSION['username']  = $row['username'];
    $_SESSION['role']      = $row['role'];
    $_SESSION['logged_in'] = true;

    return true;
}

/**
 * Log out current user
 */
function auth_logout() {
    session_destroy();
    header('Location: index.php');
    exit;
}

/**
 * Check if user is logged in
 */
function auth_check() {
    if (empty($_SESSION['logged_in'])) {
        header('Location: login.php');
        exit;
    }
}

/**
 * Require admin role
 */
function auth_require_admin() {
    auth_check();
    if ($_SESSION['role'] != 'admin') {
        die('Access denied.');
    }
}

/**
 * Register a new user — no input validation, plain SQL
 */
function auth_register($username, $email, $password) {
    // No validation at all
    $username = db_escape($username);
    $email    = db_escape($email);
    $password = md5($password);   // Insecure hash

    // Check duplicate — but race condition possible
    $exists = db_fetch_one("SELECT id FROM users WHERE email='$email'");
    if ($exists) {
        return false;
    }

    db_execute("INSERT INTO users (username, email, password, role, created_at)
                VALUES ('$username', '$email', '$password', 'user', NOW())");
    return db_last_id();
}

/**
 * Get current logged-in user data
 */
function auth_current_user() {
    if (empty($_SESSION['user_id'])) return null;
    return db_fetch_one("SELECT * FROM users WHERE id=" . (int)$_SESSION['user_id']);
}
