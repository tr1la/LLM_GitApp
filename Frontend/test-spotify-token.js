#!/usr/bin/env node

/**
 * Spotify Token Validator
 * Tests if an access token is valid and has required permissions
 */

import axios from 'axios';

const token = process.argv[2];

if (!token) {
    console.error('❌ Usage: node test-spotify-token.js <YOUR_TOKEN>');
    console.error('Example: node test-spotify-token.js BQxxxxxxxxx...');
    process.exit(1);
}

console.log('🔍 Testing Spotify Access Token...\n');

async function testToken() {
    try {
        // Test 1: Get current user info
        console.log('1️⃣  Checking user info...');
        const userRes = await axios.get('https://api.spotify.com/v1/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const user = userRes.data;
        console.log(`   ✅ User: ${user.display_name || user.id}`);
        console.log(`   ✅ Account Type: ${user.product}`);
        console.log(`   ✅ Email: ${user.email || 'N/A'}\n`);

        // Test 2: Check devices
        console.log('2️⃣  Checking available devices...');
        const devicesRes = await axios.get('https://api.spotify.com/v1/me/player/devices', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const devices = devicesRes.data.devices;
        if (devices.length === 0) {
            console.log('   ⚠️  No devices found. Open Spotify on any device and try again.');
        } else {
            console.log(`   ✅ Found ${devices.length} device(s):`);
            devices.forEach((device, idx) => {
                console.log(`      ${idx + 1}. ${device.name} (Type: ${device.type}, Active: ${device.is_active})`);
            });
        }
        console.log('');

        // Test 3: Get current playback
        console.log('3️⃣  Checking current playback...');
        const playbackRes = await axios.get('https://api.spotify.com/v1/me/player/currently-playing', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (playbackRes.data && playbackRes.data.item) {
            console.log(`   ✅ Currently playing: ${playbackRes.data.item.name}`);
        } else {
            console.log('   ℹ️  Nothing currently playing');
        }
        console.log('');

        console.log('✅ TOKEN IS VALID!\n');
        console.log('✨ You can now use this token in your .env file:');
        console.log(`VITE_SPOTIFY_ACCESS_TOKEN=${token}\n`);

    } catch (error) {
        if (error.response?.status === 401) {
            console.error('❌ TOKEN INVALID OR EXPIRED');
            console.error('   The token is not recognized by Spotify API.');
            console.error('   Get a fresh token by running: npm run spotify:token\n');
        } else if (error.response?.status === 404) {
            console.error('❌ INVALID USERNAME / WRONG ACCOUNT');
            console.error('   The token might be for a different Spotify account.');
            console.error('   Error details:', error.response.data);
            console.error('\n   Make sure you authorize with the correct Spotify account.\n');
        } else {
            console.error('❌ ERROR:', error.response?.data?.error?.message || error.message);
        }
        process.exit(1);
    }
}

testToken();
