<?php
/**
 * Homepage — mixed HTML/PHP, no templating, direct output
 */
require_once 'config.php';
require_once 'utils.php';
require_once 'products.php';
session_start();

$search    = isset($_GET['q'])   ? $_GET['q']        : '';
$category  = isset($_GET['cat']) ? (int)$_GET['cat'] : null;
$page      = isset($_GET['page'])? (int)$_GET['page']: 1;
$per_page  = 12;
$offset    = ($page - 1) * $per_page;

// Unsafe: $search passed directly to query inside get_all()
$products  = Product::get_all($category, $search);
$categories = get_categories();
$featured  = Product::get_featured(4);

$total = count($products);
$paged = array_slice($products, $offset, $per_page);

?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title><?php echo SITE_NAME; ?></title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>

<header>
    <h1><?php echo SITE_NAME; ?></h1>
    <nav>
        <a href="index.php">Home</a>
        <a href="cart.php">Cart</a>
        <?php if (!empty($_SESSION['logged_in'])): ?>
            <a href="account.php">Hello, <?php echo $_SESSION['username']; ?></a>
            <a href="logout.php">Logout</a>
        <?php else: ?>
            <a href="login.php">Login</a>
            <a href="register.php">Register</a>
        <?php endif; ?>
    </nav>
</header>

<!-- Search form - outputs $search directly (XSS risk) -->
<form method="GET" action="index.php">
    <input type="text" name="q" value="<?php echo $search; ?>" placeholder="Search...">
    <select name="cat">
        <option value="">All Categories</option>
        <?php foreach ($categories as $cat): ?>
        <option value="<?php echo $cat['id']; ?>"
            <?php echo ($category == $cat['id']) ? 'selected' : ''; ?>>
            <?php echo $cat['name']; ?>
        </option>
        <?php endforeach; ?>
    </select>
    <button type="submit">Search</button>
</form>

<?php if ($search): ?>
<p>Results for: <strong><?php echo $search; ?></strong> (<?php echo $total; ?> found)</p>
<?php endif; ?>

<!-- Featured Products -->
<?php if (!$search && !$category): ?>
<section class="featured">
    <h2>Featured Products</h2>
    <div class="grid">
    <?php foreach ($featured as $item): ?>
        <div class="product-card">
            <h3><?php echo $item['name']; ?></h3>
            <p><?php echo truncate($item['description'], 80); ?></p>
            <span class="price">$<?php echo number_format($item['price'], 2); ?></span>
            <a href="product.php?id=<?php echo $item['id']; ?>">View</a>
        </div>
    <?php endforeach; ?>
    </div>
</section>
<?php endif; ?>

<!-- Product Grid -->
<section class="products">
    <h2>Products</h2>
    <div class="grid">
    <?php foreach ($paged as $item): ?>
        <div class="product-card">
            <h3><?php echo $item['name']; ?></h3>
            <p><?php echo truncate($item['description'], 80); ?></p>
            <span class="price">$<?php echo number_format($item['price'], 2); ?></span>
            <?php if ($item['stock'] > 0): ?>
                <a href="cart.php?add=<?php echo $item['id']; ?>">Add to Cart</a>
            <?php else: ?>
                <span class="out-of-stock">Out of Stock</span>
            <?php endif; ?>
        </div>
    <?php endforeach; ?>
    </div>

    <?php echo render_pagination($total, $per_page, $page); ?>
</section>

<footer>
    <p>&copy; <?php echo date('Y'); ?> <?php echo SITE_NAME; ?></p>
</footer>

</body>
</html>
