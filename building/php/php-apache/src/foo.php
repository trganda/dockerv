<?php
if (ini_get('session.auto_start')) {
	session_destroy();
}

ini_set('session.serialize_handler', 'php_serialize');
session_start();

$_SESSION['ryat'] = $_GET['ryat'];
?>