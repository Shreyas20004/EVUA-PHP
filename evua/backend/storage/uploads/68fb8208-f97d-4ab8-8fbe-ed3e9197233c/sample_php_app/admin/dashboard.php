<?php
/**
 * Admin Dashboard — multiple SQL injection risks, deprecated functions
 */
require_once '../config.php';
require_once '../auth.php';
require_once '../utils.php';

auth_require_admin();

// Process actions from POST — no CSRF token check
if ($_SERVER['REQUEST_METHOD'] == 'POST') {

    if ($_POST['action'] == 'delete_user') {
        $uid = (int) $_POST['user_id'];
        db_execute("DELETE FROM users WHERE id=$uid AND role != 'admin'");
        $msg = 'User deleted.';
    }

    if ($_POST['action'] == 'update_product') {
        $pid   = (int)    $_POST['product_id'];
        $name  = db_escape($_POST['name']);
        $price = (float)  $_POST['price'];
        $stock = (int)    $_POST['stock'];
        db_execute("UPDATE products SET name='$name', price=$price, stock=$stock WHERE id=$pid");
        $msg = 'Product updated.';
    }

    if ($_POST['action'] == 'add_category') {
        $name = db_escape($_POST['cat_name']);
        db_execute("INSERT INTO categories (name) VALUES ('$name')");
        $msg = 'Category added.';
    }
}

// Stats — multiple queries instead of one JOIN
$user_count    = db_count("SELECT id FROM users");
$product_count = db_count("SELECT id FROM products");
$order_count   = db_count("SELECT id FROM orders");
$revenue       = db_fetch_one("SELECT SUM(total) AS rev FROM orders WHERE status='completed'");

// Recent orders — raw data, no sanitizing on output
$recent_orders = db_fetch_all("SELECT o.*, u.username, u.email
                                FROM orders o
                                JOIN users u ON u.id = o.user_id
                                ORDER BY o.created_at DESC
                                LIMIT 20");

// Low stock using deprecated mysql_ directly
$low_stock = db_fetch_all("SELECT * FROM products WHERE stock < 5 ORDER BY stock ASC");

$users = db_fetch_all("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 50");

?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Admin Dashboard</title>
</head>
<body>
<h1>Admin Dashboard</h1>

<?php if (!empty($msg)): ?>
<div class="notice"><?php echo $msg; ?></div>
<?php endif; ?>

<section>
    <h2>Stats</h2>
    <ul>
        <li>Users: <?php echo $user_count; ?></li>
        <li>Products: <?php echo $product_count; ?></li>
        <li>Orders: <?php echo $order_count; ?></li>
        <li>Revenue: $<?php echo number_format($revenue['rev'], 2); ?></li>
    </ul>
</section>

<section>
    <h2>Low Stock — Alert</h2>
    <table border="1">
        <tr><th>ID</th><th>Name</th><th>Stock</th><th>Action</th></tr>
        <?php foreach ($low_stock as $p): ?>
        <tr>
            <td><?php echo $p['id']; ?></td>
            <td><?php echo $p['name']; ?></td>
            <td><?php echo $p['stock']; ?></td>
            <td>
                <form method="POST">
                    <input type="hidden" name="action" value="update_product">
                    <input type="hidden" name="product_id" value="<?php echo $p['id']; ?>">
                    <input type="text"   name="name"  value="<?php echo $p['name']; ?>">
                    <input type="number" name="stock" value="<?php echo $p['stock']; ?>">
                    <input type="number" name="price" value="<?php echo $p['price']; ?>" step="0.01">
                    <button type="submit">Update</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
</section>

<section>
    <h2>Recent Orders</h2>
    <table border="1">
        <tr><th>ID</th><th>User</th><th>Total</th><th>Status</th><th>Date</th></tr>
        <?php foreach ($recent_orders as $o): ?>
        <tr>
            <!-- Output not escaped — XSS risk -->
            <td><?php echo $o['id']; ?></td>
            <td><?php echo $o['username']; ?> (<?php echo $o['email']; ?>)</td>
            <td>$<?php echo number_format($o['total'], 2); ?></td>
            <td><?php echo $o['status']; ?></td>
            <td><?php echo format_date($o['created_at']); ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
</section>

<section>
    <h2>Users</h2>
    <table border="1">
        <tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Joined</th><th>Action</th></tr>
        <?php foreach ($users as $u): ?>
        <tr>
            <td><?php echo $u['id']; ?></td>
            <td><?php echo $u['username']; ?></td>
            <td><?php echo $u['email']; ?></td>
            <td><?php echo $u['role']; ?></td>
            <td><?php echo format_date($u['created_at']); ?></td>
            <td>
                <?php if ($u['role'] != 'admin'): ?>
                <form method="POST" onsubmit="return confirm('Delete user?')">
                    <input type="hidden" name="action"  value="delete_user">
                    <input type="hidden" name="user_id" value="<?php echo $u['id']; ?>">
                    <button type="submit">Delete</button>
                </form>
                <?php endif; ?>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
</section>

<section>
    <h2>Add Category</h2>
    <form method="POST">
        <input type="hidden" name="action" value="add_category">
        <input type="text" name="cat_name" placeholder="Category name" required>
        <button type="submit">Add</button>
    </form>
</section>
</body>
</html>
