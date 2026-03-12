<?php
/**
 * Utility functions — mix of working and deprecated PHP
 */

/**
 * Sanitize output — but uses htmlspecialchars inconsistently
 */
function h($str) {
    return htmlspecialchars($str);
}

/**
 * Redirect helper
 */
function redirect($url) {
    header("Location: $url");
    exit;
}

/**
 * Split a comma-separated string — split() removed in PHP 7
 */
function explode_tags($tagstring) {
    return split(',', $tagstring);   // split() removed in PHP 7, use explode()
}

/**
 * Check if string matches pattern — ereg removed in PHP 7
 */
function is_valid_email($email) {
    return eregi('^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', $email);
}

/**
 * Format a MySQL date
 */
function format_date($mysql_date) {
    $ts = strtotime($mysql_date);
    return date('d M Y', $ts);
}

/**
 * Truncate a string
 */
function truncate($str, $len = 100) {
    if (strlen($str) <= $len) return $str;
    return substr($str, 0, $len) . '...';
}

/**
 * Get client IP — unreliable, spoofable
 */
function get_ip() {
    if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        return $_SERVER['HTTP_X_FORWARDED_FOR'];  // Can be spoofed
    }
    return $_SERVER['REMOTE_ADDR'];
}

/**
 * Log an event to a file
 */
function log_event($message) {
    $line = date('Y-m-d H:i:s') . ' | ' . $message . PHP_EOL;
    file_put_contents('/tmp/app.log', $line, FILE_APPEND);
}

/**
 * Generate a token — weak randomness
 */
function generate_token() {
    return md5(uniqid(rand(), true));  // Should use random_bytes()
}

/**
 * Magic quotes compat — PHP 5.3 removed them but old code still checks
 */
function strip_slashes_deep($value) {
    if (get_magic_quotes_gpc()) {
        $value = is_array($value)
            ? array_map('stripslashes', $value)
            : stripslashes($value);
    }
    return $value;
}

/**
 * Render a simple pagination bar
 */
function render_pagination($total, $per_page, $current_page) {
    $pages = ceil($total / $per_page);
    if ($pages <= 1) return '';

    $html = '<div class="pagination">';
    for ($i = 1; $i <= $pages; $i++) {
        $active = ($i == $current_page) ? ' active' : '';
        $html  .= "<a href='?page=$i' class='page$active'>$i</a> ";
    }
    $html .= '</div>';
    return $html;
}
