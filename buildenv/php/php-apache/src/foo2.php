<?php

ini_set('session.serialize_handler', 'php');
// or session.serialize_handler set to php in php.ini 
session_start();

class ryat {
	var $hi;
	
	function __wakeup() {
		print("hi");
	}
	function __destruct() {
		echo $this->hi;
	}
}

?>