<?php
/**
 * Orders — complex legacy patterns
 * Uses: call_user_func, deprecated each(), list(), old-style exceptions
 */
require_once 'db.php';
require_once 'utils.php';

/**
 * Create an order — no transaction, no prepared statements
 */
function create_order($user_id, $cart_items) {
    $user_id = (int) $user_id;
    $total   = 0;

    // Calculate total using deprecated each()
    reset($cart_items);
    while (list($product_id, $qty) = each($cart_items)) {  // each() removed in PHP 8
        $p      = db_fetch_one("SELECT price FROM products WHERE id=" . (int)$product_id);
        $total += $p['price'] * $qty;
    }

    $total = round($total, 2);

    db_execute("INSERT INTO orders (user_id, total, status, created_at)
                VALUES ($user_id, $total, 'pending', NOW())");
    $order_id = db_last_id();

    // Insert order items
    foreach ($cart_items as $product_id => $qty) {
        $product_id = (int) $product_id;
        $qty        = (int) $qty;
        $p  = db_fetch_one("SELECT price FROM products WHERE id=$product_id");
        $subtotal = $p['price'] * $qty;
        db_execute("INSERT INTO order_items (order_id, product_id, qty, price)
                    VALUES ($order_id, $product_id, $qty, $subtotal)");
        // Decrement stock — no check if stock is sufficient
        db_execute("UPDATE products SET stock = stock - $qty WHERE id=$product_id");
    }

    return $order_id;
}

/**
 * Get order with items
 */
function get_order($order_id) {
    $order_id = (int) $order_id;
    $order    = db_fetch_one("SELECT o.*, u.username, u.email
                               FROM orders o
                               JOIN users u ON u.id = o.user_id
                               WHERE o.id=$order_id");

    if (!$order) return false;

    $order['items'] = db_fetch_all("SELECT oi.*, p.name AS product_name
                                    FROM order_items oi
                                    JOIN products p ON p.id = oi.product_id
                                    WHERE oi.order_id=$order_id");
    return $order;
}

/**
 * Update order status — old-style callback mapping
 */
function update_order_status($order_id, $status) {
    // Map status to handler using call_user_func (old pattern)
    $handlers = array(
        'completed' => 'on_order_completed',
        'cancelled' => 'on_order_cancelled',
        'shipped'   => 'on_order_shipped',
    );

    $order_id = (int) $order_id;
    db_execute("UPDATE orders SET status='".db_escape($status)."' WHERE id=$order_id");

    if (isset($handlers[$status])) {
        call_user_func($handlers[$status], $order_id);
    }
}

function on_order_completed($order_id) {
    log_event("Order $order_id completed");
}

function on_order_cancelled($order_id) {
    $order = get_order($order_id);
    // Restore stock
    foreach ($order['items'] as $item) {
        db_execute("UPDATE products SET stock = stock + {$item['qty']} WHERE id={$item['product_id']}");
    }
    log_event("Order $order_id cancelled, stock restored");
}

function on_order_shipped($order_id) {
    log_event("Order $order_id shipped");
}

/**
 * User order history
 */
function get_user_orders($user_id) {
    $user_id = (int) $user_id;
    return db_fetch_all("SELECT * FROM orders WHERE user_id=$user_id ORDER BY created_at DESC");
}

/**
 * Old-style exception handling
 */
function process_payment($order_id, $card_data) {
    try {
        // No real payment — placeholder
        if (empty($card_data['number'])) {
            throw new Exception('Card number required');
        }
        update_order_status($order_id, 'completed');
        return true;
    } catch (Exception $e) {
        log_event('Payment failed: ' . $e->getMessage());
        return false;
    }
}
