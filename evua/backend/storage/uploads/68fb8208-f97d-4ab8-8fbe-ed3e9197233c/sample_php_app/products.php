<?php
/**
 * Products — direct SQL string concat, no prepared statements
 * ereg_* functions removed in PHP 7
 */
require_once 'db.php';

class Product {

    var $id;
    var $name;
    var $description;
    var $price;
    var $stock;
    var $category_id;

    // Old PHP 4 constructor
    function Product($id = null) {
        if ($id) $this->load($id);
    }

    function load($id) {
        $row = db_fetch_one("SELECT * FROM products WHERE id=" . (int)$id);
        if ($row) {
            foreach ($row as $k => $v) {
                $this->$k = $v;
            }
        }
    }

    // Deprecated ereg functions (removed in PHP 7)
    function validate_price($price) {
        return ereg('^[0-9]+(\.[0-9]{1,2})?$', $price);
    }

    function validate_name($name) {
        return eregi('^[a-z0-9 _-]+$', $name);
    }

    function save() {
        $name        = db_escape($this->name);
        $description = db_escape($this->description);
        $price       = (float) $this->price;
        $stock       = (int)   $this->stock;
        $cat         = (int)   $this->category_id;

        if ($this->id) {
            db_execute("UPDATE products
                        SET name='$name', description='$description',
                            price=$price, stock=$stock, category_id=$cat
                        WHERE id={$this->id}");
        } else {
            db_execute("INSERT INTO products (name, description, price, stock, category_id)
                        VALUES ('$name','$description',$price,$stock,$cat)");
            $this->id = db_last_id();
        }
    }

    // Static methods old-style
    function get_all($category = null, $search = null) {
        $sql = "SELECT p.*, c.name AS category_name
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                WHERE 1=1";

        if ($category) {
            $sql .= " AND p.category_id=" . (int)$category;
        }

        // Dangerous: $search is user input with no escaping here
        if ($search) {
            $sql .= " AND (p.name LIKE '%$search%' OR p.description LIKE '%$search%')";
        }

        $sql .= " ORDER BY p.name ASC";
        return db_fetch_all($sql);
    }

    function get_featured($limit = 6) {
        return db_fetch_all("SELECT * FROM products WHERE featured=1 ORDER BY RAND() LIMIT $limit");
    }

    function decrement_stock($qty = 1) {
        db_execute("UPDATE products SET stock = stock - $qty WHERE id={$this->id}");
    }

    function format_price() {
        return '$' . number_format($this->price, 2);
    }
}

/**
 * Search products — raw $_GET used directly (XSS + SQLi risk)
 */
function search_products() {
    $search = $_GET['q'];   // No sanitization
    return db_fetch_all("SELECT * FROM products
                         WHERE name LIKE '%$search%'
                         OR description LIKE '%$search%'");
}

/**
 * Category helpers
 */
function get_categories() {
    return db_fetch_all("SELECT * FROM categories ORDER BY name");
}

function get_category_name($id) {
    $row = db_fetch_one("SELECT name FROM categories WHERE id=" . (int)$id);
    return $row ? $row['name'] : 'Unknown';
}
