<?php
/**
 * Database Helper
 * Legacy mysql_ functions — removed in PHP 7
 */
require_once 'config.php';

/**
 * Run a query and return all rows
 */
function db_fetch_all($sql) {
    $result = mysql_query($sql);
    if (!$result) {
        die('Query failed: ' . mysql_error() . ' | SQL: ' . $sql);
    }
    $rows = array();
    while ($row = mysql_fetch_assoc($result)) {
        $rows[] = $row;
    }
    mysql_free_result($result);
    return $rows;
}

/**
 * Run a query and return one row
 */
function db_fetch_one($sql) {
    $result = mysql_query($sql);
    if (!$result) {
        return false;
    }
    return mysql_fetch_assoc($result);
}

/**
 * Execute an INSERT/UPDATE/DELETE
 */
function db_execute($sql) {
    $result = mysql_query($sql);
    if (!$result) {
        die('Execute failed: ' . mysql_error());
    }
    return mysql_affected_rows();
}

/**
 * Get last inserted ID
 */
function db_last_id() {
    return mysql_insert_id();
}

/**
 * Escape a value for use in queries (old style - no prepared statements)
 */
function db_escape($value) {
    return mysql_real_escape_string($value);
}

/**
 * Count rows in result
 */
function db_count($sql) {
    $result = mysql_query($sql);
    return mysql_num_rows($result);
}
