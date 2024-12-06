<?php
$GATEWAY_URL_INSIDE_CONTAINER = 'https://gateway:5000';
//$GATEWAY_URL_OUTSIDE_CONTAINER = 'https://localhost:5001';
$BALANCE_INCREASE_AMOUNT = 30;

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
        'amount' => $BALANCE_INCREASE_AMOUNT
    ]);
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


// Handle roll gatcha
if (isset($_POST['roll_gatcha'])) {
    if ($balance < 10) {
        echo "<script>
            document.addEventListener('DOMContentLoaded', function() {
                Swal.fire({
                    title: 'Error!',
                    text: 'Insufficient balance to roll gatcha. Please increase your balance.',
                    icon: 'error',
                    confirmButtonText: 'Okay'
                });
            });
        </script>";
    } else {
        $response = api_call('GET', '/gatcha/roll');

        if (empty($response['message'])) {
            echo "<script>
                document.addEventListener('DOMContentLoaded', function() {
                    Swal.fire({
                        title: 'Error!',
                        text: 'Failed to roll gatcha. Please try again.',
                        icon: 'error',
                        confirmButtonText: 'Okay'
                    });
                });
            </script>";
        } else {
            $roll_message = $response['message'];
            $name = $response['gatcha']['name'];
            $rarity = $response['gatcha']['rarity'];
            $image = $response['gatcha']['image'];
            $imageUrl = "proxy.php?url=" . urlencode($GATEWAY_URL_INSIDE_CONTAINER . $image);
            echo "<script>
                document.addEventListener('DOMContentLoaded', function() {
                    Swal.fire({
                        title: 'Congratulations!',
                        text: 'You rolled a " . htmlspecialchars($name) . " (" . htmlspecialchars($rarity) . ")',
                        imageUrl: '" . htmlspecialchars($imageUrl ) . "',
                        imageWidth: 300,
                        imageHeight: 'auto',
                        imageAlt: 'Gatcha Image',
                        confirmButtonText: 'Awesome!'
                    });
                });
            </script>";
        }
    }
}



// Fetch balance and gachas again
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
<head>
    <meta charset="UTF-8">
    <title>User Dashboard</title>
    <!-- Pico CSS -->
    <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
    <!-- Boxicons for Icons -->
    <link href='https://unpkg.com/boxicons@2.1.4/css/boxicons.min.css' rel='stylesheet'>

    <style>
        main.container {
            max-width: 800px;
            margin: 0 auto;
        }
        .flex {
            display: flex;
            gap: 2rem;
        }
        form {
            width: 100%;
        }
        .error {
            color: var(--color-danger);
        }
        .success {
            color: var(--color-success);
        }
    </style>
</head>
<body>
<main class="container">
    <?php if (!isset($_SESSION['token'])): ?>
        <h1>Welcome to Lady Gatcha</h1>
        <p>Please login or register to continue.</p>
        <br />
        <div class="flex">
            <div>
                <h2>Login</h2>
                <?php if (isset($error) && !isset($_POST['register'])): ?>
                    <p class="error"><?php echo htmlspecialchars($error); ?></p>
                <?php endif; ?>
                <form method="post">
                    <label for="username"><i class='bx bx-user'></i> Username</label>
                    <input type="text" name="username" required placeholder="Enter your username">
                    <label for="password"><i class='bx bx-lock'></i> Password</label>
                    <input type="password" name="password" required placeholder="Enter your password">
                    <button type="submit" name="login" class="contrast">
                        <i class='bx bx-log-in'></i> Login
                    </button>
                </form>
            </div>
            <div>
                <h2>Register</h2>
                <?php if (isset($register_message)): ?>
                    <p class="success"><?php echo htmlspecialchars($register_message); ?></p>
                <?php endif; ?>
                <?php if (isset($error) && isset($_POST['register'])): ?>
                    <p class="error"><?php echo htmlspecialchars($error); ?></p>
                <?php endif; ?>
                <form method="post">
                    <label for="username"><i class='bx bx-user'></i> Username</label>
                    <input type="text" name="username" required placeholder="Choose a username">
                    <label for="password"><i class='bx bx-lock'></i> Password</label>
                    <input type="password" name="password" required placeholder="Choose a password">
                    <label for="email"><i class='bx bx-envelope'></i> Email</label>
                    <input type="email" name="email" required placeholder="Enter your email">
                    <button type="submit" name="register" class="contrast">
                        <i class='bx bx-user-plus'></i> Register
                    </button>
                </form>
            </div>
        </div>
        <?php else: ?>
            <article>
                <header>
                    <h1>Welcome to <b>Lady Gatcha</b></h1>
                </header>
                <p><strong>User UUID:</strong> <?php echo htmlspecialchars($_SESSION['userID'] ?? 'N/A'); ?></p>
                <p><strong>Gagabucks Balance:</strong> <?php echo htmlspecialchars($balance); ?> G$</p>
            </article>
            <form method="post" class="grid">
                <button type="submit" name="increase_balance" class="contrast">
                    <i class='bx bx-money'></i> Add Balance (+<?=$BALANCE_INCREASE_AMOUNT?>G$)
                </button>
                <button type="submit" name="roll_gatcha" class="contrast">
                    <i class='bx bx-dice-5'></i> Roll Gatcha
                </button>
                <button type="submit" name="logout" class="contrast">
                    <i class='bx bx-log-out'></i> Logout
                </button>
            </form>
        
            <h2>Your Gatcha Collection</h2>
            <div class="grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem;">
                <?php foreach ($gatcha_data as $index => $gatcha): ?>
                    <article class="card">
                        <header>
                            <?php if (in_array($gatcha['_id'], $user_gatcha_ids)): ?>
                                <img src="proxy.php?url=<?php echo urlencode($GATEWAY_URL_INSIDE_CONTAINER . $gatcha['image']); ?>" alt="<?php echo htmlspecialchars($gatcha['name']); ?>">
                            <?php else: ?>
                                <img src="/mistery.webp" alt="Mistery Gatcha">
                            <?php endif; ?>
                            <h3><?php echo htmlspecialchars($gatcha['name']); ?></h3>
                        </header>
                        <p>Rarity: <?php echo htmlspecialchars($gatcha['rarity']); ?></p>
                        <p>Gatcha ID: <?php echo htmlspecialchars($gatcha['_id']); ?></p>
                        <?php if (in_array($gatcha['_id'], $user_gatcha_ids)): ?>
                            <p class="owned" style="color: #28a745; font-weight: bold;">🎉 You own this gatcha! 🎉</p>
                        <?php else: ?>
                            <p class="not-owned" style="color: #dc3545; font-weight: bold;">😢 Not in your collection yet! 😢</p>
                        <?php endif; ?>
                    </article>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
</main>
</body>
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
</html>