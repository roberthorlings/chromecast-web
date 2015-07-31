#!/usr/bin/php
<?php
	// SETTINGS
	define( "DEBUG", 0 );
	define( "MAX_TRIES", 20 );

	$tokenUrl = "http://ida.omroep.nl/npoplayer/i.js";
	$streamUrl = "http://ida.omroep.nl/aapi/?type=jsonp&callback=streamMethod";
	
	$availableChannels = [
		"npo1" => [ 
			"stream" => "http://livestreams.omroep.nl/live/npo/tvlive/ned1/ned1.isml/ned1.m3u8",
			"title" => "NPO 1",
			"icon" => "http://mediadb.omroep.nl/assets/001/504/521/512x341.png"
		],
		"npo2" => [ 
			"stream" => "http://livestreams.omroep.nl/live/npo/tvlive/ned2/ned2.isml/ned2.m3u8",
			"title" => "NPO 2",
			"icon" => "http://mediadb.omroep.nl/assets/001/504/522/512x341.png"
		],
		"npo3" => [ 
			"stream" => "http://livestreams.omroep.nl/live/npo/tvlive/ned3/ned3.isml/ned3.m3u8",
			"title" => "NPO 3",
			"icon" => "http://mediadb.omroep.nl/assets/001/504/523/512x341.png"
		],
		"journaal24" => [ 
			"stream" => "http://livestreams.omroep.nl/live/npo/thematv/journaal24/journaal24.isml/journaal24.m3u8",
			"title" => "NPO Nieuws",
			"icon" => "http://mediadb.omroep.nl/assets/001/504/519/512x341.png"
		],
		"politiek24" => 
		[ 
			"stream" => "http://livestreams.omroep.nl/live/npo/thematv/politiek24/politiek24.isml/politiek24.m3u8",
			"title" => "NPO Politiek",
			"icon" => "http://mediadb.omroep.nl/assets/001/504/520/512x341.png"
		],
		"hollanddoc" =>[ 
			"stream" => "http://livestreams.omroep.nl/live/npo/thematv/hollanddoc24/hollanddoc24.isml/hollanddoc24.m3u8",
			"title" => "NPO Doc",
			"icon" => "http://mediadb.omroep.nl/assets/001/504/517/512x341.png"
		],
		 
		
	];
	// END OF SETTINGS
	
	function exitWithError( $message ) {
		echo json_encode([
			"success" => false,
			"error" => $message
		]);
		die();
	}

	// Determine which livestream URL to use
	if( $argc > 1 ) {
		$channel = $argv[1];
	} else {
		$channel = "npo1";
	}

	if( !array_key_exists( $channel, $availableChannels ) ) {
		exitWithError( "Invalid channel: $channel. Available channels: " . implode( ", ", array_keys( $availableChannels ) ) );
	}

	if( DEBUG )
		echo "Retrieving data for $channel\n";

	$channelData = $availableChannels[$channel];
	$liveStreamUrl = $channelData["stream"];

	// Keep on repeating the process as it seems to randomly return the url or not
	$i = 0;
	$streamUrlWithHash = null;
	while( $i < MAX_TRIES && !$streamUrlWithHash ) {
		// Retrieve token
		$url = $tokenUrl . "?s=" . urlencode($liveStreamUrl) . "&_=" . ( mktime() * 1000);

		if( DEBUG )
			echo "Retrieving token from " . $url . "\n";

		$tokenJs = file_get_contents( $url );
	
		if( !preg_match("/\"(.+)\"/", $tokenJs, $matches) ) {
			exitWithError( "Cannot extract token from token javascript." );
		}
	
		$token = $matches[1];
		if( DEBUG )
			echo "Token received : $token\n";

		// Retrieve stream URL with token
		$url = $streamUrl . "&stream=" . urlencode($liveStreamUrl) . "&token=" . $token . "&_=" . ( mktime() * 1000 );

		if( DEBUG )
			echo "Retrieving stream URL with hash from " . $url . "\n";

		$streamJs = file_get_contents( $url );

		if( !preg_match( "/^streamMethod\((.*)\)$/", $streamJs, $matches ) ) {
			exitWithError( "Cannot extract json from jsonP message" );
		}

		$streamJson = json_decode($matches[1]);
		if( !$streamJson ) {
			exitWithError( "No proper json received" );
		}

		if( $streamJson->success ) {
			$streamUrlWithHash = $streamJson->stream;
			if( DEBUG )
				echo "Stream URL received: " . $streamUrlWithHash . "\n";
		}
		
		// Increase iteration number
		$i++;
	}
	
	if( !$streamUrlWithHash ) {
		exitWithError( "No URL could be retrieved in " . MAX_TRIES . " tries" );
	}

	// Now retrieve the actual URL
	$url = $streamUrlWithHash . "&callback=finalMethod&_=" . (mktime() * 1000);
	$finalJs = file_get_contents($url);

	if( !preg_match("/\"(.+)\"/", $finalJs, $matches) ) {
		exitWithError( "No proper response from stream URL with hash" );
	}

	$finalUrl = json_decode($matches[0]);
	
	if( DEBUG )
		echo "Final URL: ";
	
	// Store final URL
	$channelData[ "stream" ] = $finalUrl;
	$channelData[ "success" ] = true;
	echo json_encode( $channelData );
	echo "\n";
	
