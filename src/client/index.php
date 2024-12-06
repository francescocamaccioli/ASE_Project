<?php
$GATEWAY_URL_INSIDE_CONTAINER = 'https://gateway:5000';
$GATEWAY_URL_OUTSIDE_CONTAINER = 'https://localhost:5001';

// Start session to store user data
session_start();

// Function to perform API calls
function api_call($method, $url, $data = null) {
    global $GATEWAY_URL_INSIDE_CONTAINER;
    $curl = curl_init();

    // Set options
    curl_setopt($curl, CURLOPT_URL, $GATEWAY_URL_INSIDE_CONTAINER . $url);
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);

    // Suppress SSL certificate verification
    curl_setopt($curl, CURLOPT_SSL_VERIFYHOST, 0);
    curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, 0);

    // Set method
    switch ($method) {
        case 'POST':
            curl_setopt($curl, CURLOPT_POST, 1);
            if ($data)
                curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($data));
            break;
        case 'GET':
            if ($data)
                curl_setopt($curl, CURLOPT_URL, $GATEWAY_URL_INSIDE_CONTAINER . $url . '?' . http_build_query($data));
            break;
    }

    // Headers
    $headers = ['Content-Type: application/json'];
    if (isset($_SESSION['token'])) {
        $headers[] = 'Authorization: Bearer ' . $_SESSION['token'];
    }
    curl_setopt($curl, CURLOPT_HTTPHEADER, $headers);

    // Execute
    $result = curl_exec($curl);
    if (!$result) {
        die("Connection Failure: " . curl_error($curl));
    }
    curl_close($curl);
    return json_decode($result, true);
}

// Handle logout
if (isset($_POST['logout'])) {
    session_destroy();
    header("Location: " . $_SERVER['PHP_SELF']);
    exit();
}

// Handle login
if (isset($_POST['login'])) {
    $username = $_POST['username'];
    $password = $_POST['password'];

    $response = api_call('POST', '/auth/login', [
        'username' => $username,
        'password' => $password
    ]);

    if (isset($response['access_token']) && isset($response['userID'])) {
        $_SESSION['token'] = $response['access_token'];
        $_SESSION['userID'] = $response['userID'];
    } else {
        $error = $response['error'] ?? 'Login failed';
    }
}

// Handle register
if (isset($_POST['register'])) {
    $username = $_POST['username'];
    $password = $_POST['password'];
    $email = $_POST['email'];

    $response = api_call('POST', '/auth/register', [
        'username' => $username,
        'password' => $password,
        'email' => $email
    ]);

    if (isset($response['message'])) {
        $register_message = $response['message'];
    } else {
        $error = $response['error'] ?? 'Registration failed';
    }
}

// Handle increase balance
if (isset($_POST['increase_balance'])) {
    $response = api_call('POST', '/user/increase_balance', [
        'userID' => $_SESSION['userID'],
        'amount' => 500
    ]);
}

// Handle roll gatcha
if (isset($_POST['roll_gatcha'])) {
    $response = api_call('GET', '/gatcha/roll');

    if(empty($response['message'])){
        return;
    }

    $roll_message = $response['message'];
    $name = $response['gatcha']['name'];
    $rarity = $response['gatcha']['rarity'];
    $image = $response['gatcha']['image'];

    echo "<script>
        document.addEventListener('DOMContentLoaded', function() {
            Swal.fire({
                title: 'Congratulations!',
                text: 'You rolled a " . htmlspecialchars($name) . " (" . htmlspecialchars($rarity) . ")',
                imageUrl: '" . htmlspecialchars($GATEWAY_URL_OUTSIDE_CONTAINER . $image) . "',
                imageWidth: 400,
                imageHeight: 200,
                imageAlt: 'Gatcha Image',
                confirmButtonText: 'Awesome!'
            });
        });
    </script>";
}

// Fetch user info
if (isset($_SESSION['token'])) {
    $user_data = api_call('GET', '/user/balance');
    $balance = $user_data['balance'] ?? 0;

    // Fetch gatcha collection
    $gatcha_data = api_call('GET', '/gatcha/gatchas');

    // Fetch user's gatchas
    $user_gatcha_data = api_call('GET', '/user/collection');
    $user_gatcha_ids =$user_gatcha_data;
}
?>

<!DOCTYPE html>
<html lang="en">
<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"
>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Dashboard</title>
    <style>
        img {
            max-width: 100%;
        }
        .owned {
            color: green;
        }
        .not-owned {
            color: red;
        }
    </style>
</head>
<body>
<main class="container">
    <?php if (!isset($_SESSION['token'])): ?>
        <h1>Home</h1>
        <div style="display: flex; justify-content: space-around;">
            <div>
                <h2>Login</h2>
                <?php if (isset($error) && !isset($_POST['register'])): ?>
                    <p style="color:red;"><?php echo htmlspecialchars($error); ?></p>
                <?php endif; ?>
                <form method="post">
                    <label for="username">Username</label>
                    <input type="text" name="username" required>
                    <label for="password">Password</label>
                    <input type="password" name="password" required>
                    <button type="submit" name="login" class="contrast">Login</button>
                </form>
            </div>
            <div>
                <h2>Register</h2>
                <?php if (isset($register_message)): ?>
                    <p style="color:green;"><?php echo htmlspecialchars($register_message); ?></p>
                <?php endif; ?>
                <?php if (isset($error) && isset($_POST['register'])): ?>
                    <p style="color:red;"><?php echo htmlspecialchars($error); ?></p>
                <?php endif; ?>
                <form method="post">
                    <label for="username">Username</label>
                    <input type="text" name="username" required>
                    <label for="password">Password</label>
                    <input type="password" name="password" required>
                    <label for="email">Email</label>
                    <input type="email" name="email" required>
                    <button type="submit" name="register" class="contrast">Register</button>
                </form>
            </div>
        </div>
    <?php else: ?>
        <h1>Welcome to <b>Lady Gatcha</b></h1>
        <p>UUID: <?php echo htmlspecialchars($_SESSION['userID'] ?? 'N/A'); ?></p>
        <p>Balance: <?php echo htmlspecialchars($balance); ?></p>
        <form method="post">
            <button type="submit" name="increase_balance">Increase Balance</button>
            <button type="submit" name="roll_gatcha">Roll Gatcha</button>
            <button type="submit" name="logout">Logout</button>
        </form>
        <?php if (isset($roll_message)): ?>
            <p><?php echo htmlspecialchars($roll_message); ?></p>
        <?php endif; ?>

        <h2>Your Gatcha Collection</h2>
        <div class="grid">
            <?php foreach ($gatcha_data as $gatcha): ?>
                <div class="card">
                                        <img src="proxy.php?url=<?php echo urlencode($GATEWAY_URL_INSIDE_CONTAINER . $gatcha['image']); ?>" alt="<?php echo htmlspecialchars($gatcha['name']); ?>">
                    <h3><?php echo htmlspecialchars($gatcha['name']); ?></h3>
                    <p>Rarity: <?php echo htmlspecialchars($gatcha['rarity']); ?></p>
                    <p>Gatcha ID: <?php echo htmlspecialchars($gatcha['_id']); ?></p>
                    <?php if (in_array($gatcha['_id'], $user_gatcha_ids)): ?>
                        <p class="owned">Owned</p>
                    <?php else: ?>
                        <p class="not-owned">Not Owned</p>
                    <?php endif; ?>
                </div>
            <?php endforeach; ?>
        </div>
    <?php endif; ?>
</main>
</body>
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
</html>