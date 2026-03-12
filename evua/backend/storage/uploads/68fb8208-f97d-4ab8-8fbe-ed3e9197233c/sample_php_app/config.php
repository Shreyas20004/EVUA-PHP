<?php
/**
 * Database Configuration
 * Legacy PHP 5.x style - uses mysql_ functions
 */

define('DB_HOST', 'localhost');
define('DB_USER', 'root');
define('DB_PASS', 'secret123');
define('DB_NAME', 'shop_db');

define('SITE_URL', 'http://localhost');
define('SITE_NAME', 'My Shop');
define('VERSION', '1.0');

// Old-style error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Timezone (old approach)
date_default_timezone_set('UTC');

// Connect to database using deprecated mysql_ functions
$conn = mysql_connect(DB_HOST, DB_USER, DB_PASS);
if (!$conn) {
    die('Could not connect: ' . mysql_error());
}
mysql_select_db(DB_NAME, $conn);
mysql_query("SET NAMES 'utf8'");
