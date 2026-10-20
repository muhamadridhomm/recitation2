<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { appState } from '$lib/store.svelte';

	let { children } = $props();

	let isLoggedIn = $state(false);
	let token = $state('');

	// Auth Modal State
	let showAuthModal = $state(false);
	let isLoginMode = $state(true);
	let authEmail = $state('');
	let authPassword = $state('');
	let authUsername = $state('');
	let authError = $state('');
	let isLoading = $state(false);

	onMount(() => {
		token = localStorage.getItem('token') || '';
		if (token) {
			isLoggedIn = true;
		}
	});

	function handleLogout() {
		localStorage.removeItem('token');
		isLoggedIn = false;
		// Optionally redirect to home
		window.location.href = '/';
	}

	async function handleAuth(e: Event) {
		e.preventDefault();
		isLoading = true;
		authError = '';
		try {
			if (isLoginMode) {
				const formData = new URLSearchParams();
				formData.append('username', authEmail);
				formData.append('password', authPassword);
				const res = await fetch('http://localhost:8000/api/auth/login', {
					method: 'POST',
					headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
					body: formData
				});
				if (!res.ok) throw new Error('Invalid credentials');
				const data = await res.json();
				localStorage.setItem('token', data.access_token);
				isLoggedIn = true;
				showAuthModal = false;
				window.location.reload(); // Reload to refresh page data
			} else {
				const res = await fetch('http://localhost:8000/api/auth/register', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ email: authEmail, password: authPassword, username: authUsername })
				});
				if (!res.ok) {
					const data = await res.json();
					throw new Error(data.detail || 'Registration failed');
				}
				isLoginMode = true;
				await handleAuth(e);
			}
		} catch (err: any) {
			authError = err.message;
		} finally {
			isLoading = false;
		}
	}
</script>

{#if isLoggedIn}
	<!-- Logged In: Sidebar Layout -->
	<div class="min-h-screen bg-gray-50 flex flex-col md:flex-row font-sans" dir="ltr">
		<!-- Sidebar -->
		<aside class="w-full md:w-64 bg-white border-b md:border-b-0 md:border-r border-gray-200 flex flex-col shrink-0">
			<div class="p-6 border-b border-gray-100 flex justify-between items-center md:block">
				<div>
					<h1 class="text-xl font-bold text-emerald-800">Islamic Notes</h1>
					<p class="text-xs text-gray-500">Student Workspace</p>
				</div>
			</div>
			<nav class="flex-1 p-4 flex md:flex-col gap-2 overflow-x-auto whitespace-nowrap">
				<a href="/" class="px-4 py-2 rounded-md font-medium transition flex items-center gap-2 {$page.url.pathname === '/' ? 'bg-emerald-50 text-emerald-700 font-bold' : 'text-gray-600 hover:bg-gray-50'}">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
					Search Home
				</a>
				<a href="/quran" class="px-4 py-2 rounded-md font-medium transition flex items-center gap-2 {$page.url.pathname === '/quran' ? 'bg-emerald-50 text-emerald-700 font-bold' : 'text-gray-600 hover:bg-gray-50'}">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
					Al-Qur'an
				</a>
				<a href="/books" class="px-4 py-2 rounded-md font-medium transition flex items-center gap-2 {$page.url.pathname === '/books' ? 'bg-emerald-50 text-emerald-700 font-bold' : 'text-gray-600 hover:bg-gray-50'}">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
					Books Library
				</a>
				
				<hr class="my-2 md:block hidden border-gray-100">
				
				<a href="/my-notes" class="px-4 py-2 rounded-md font-medium transition flex items-center gap-2 {$page.url.pathname === '/my-notes' ? 'bg-emerald-50 text-emerald-700 font-bold' : 'text-gray-600 hover:bg-gray-50'}">
					My Projects
				</a>
				<div class="md:mt-auto flex flex-col gap-2">
					<a href="/config" class="px-4 py-2 rounded-md font-medium transition flex items-center gap-2 {$page.url.pathname === '/config' ? 'bg-emerald-50 text-emerald-700 font-bold' : 'text-gray-600 hover:bg-gray-50'}">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
						App Config
					</a>
					<button onclick={handleLogout} class="px-4 py-2 text-red-600 hover:bg-red-50 rounded-md font-bold transition flex items-center gap-2 text-left">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
						Logout
					</button>
				</div>
			</nav>
		</aside>
		
		<!-- Main Content Wrapper -->
		<div class="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
			{@render children()}
		</div>
	</div>
{:else}
	<!-- Not Logged In: Topbar Layout -->
	<div class="min-h-screen bg-gray-50 flex flex-col font-sans" dir="ltr">
		<!-- Topbar -->
		<header class="w-full flex justify-between items-center px-6 py-4 bg-white border-b border-gray-200 sticky top-0 z-30 shadow-sm shrink-0">
			<div class="flex items-center gap-8">
				<a href="/" class="text-xl font-bold text-emerald-800 tracking-tight">Islamic Notes</a>
				<nav class="hidden md:flex gap-5 text-gray-600 font-medium text-sm items-center">
					<a href="/quran" class="hover:text-emerald-700 transition flex items-center gap-1 {$page.url.pathname === '/quran' ? 'text-emerald-700 font-bold border-b-2 border-emerald-600 pb-0.5' : ''}">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
						Al-Qur'an
					</a>
					<a href="/books" class="hover:text-emerald-700 transition {$page.url.pathname === '/books' ? 'text-emerald-700 font-bold border-b-2 border-emerald-600 pb-0.5' : ''}">Books Library</a>
				</nav>
			</div>
			<div class="flex items-center gap-3">
				<select 
					bind:value={appState.language}
					class="bg-gray-100 border border-gray-200 text-gray-700 text-xs rounded-md focus:ring-emerald-500 focus:border-emerald-500 block p-2 outline-none font-bold mr-2"
				>
					<option value="en">🇺🇸 EN</option>
					<option value="ar">🇸🇦 AR</option>
					<option value="id">🇮🇩 ID</option>
				</select>
				<button onclick={() => { showAuthModal = true; isLoginMode = true; }} class="text-gray-600 font-medium text-sm hover:text-emerald-700 transition">Login</button>
				<button onclick={() => { showAuthModal = true; isLoginMode = false; }} class="bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2 rounded-md font-bold text-sm transition">Sign Up</button>
			</div>
		</header>
		
		<!-- Main Content Wrapper -->
		<div class="flex-1 flex flex-col min-w-0">
			{@render children()}
		</div>
	</div>
{/if}

<!-- Auth Modal (Global) -->
{#if showAuthModal}
	<div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
		<div class="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden flex flex-col relative" dir="ltr">
			<button onclick={() => showAuthModal = false} class="absolute top-4 right-4 text-gray-400 hover:text-gray-700">
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
			</button>
			
			<div class="p-8">
				<h3 class="text-2xl font-bold text-gray-800 mb-6">{isLoginMode ? 'Welcome Back' : 'Create an Account'}</h3>
				
				{#if authError}
					<div class="bg-red-50 text-red-700 p-3 rounded-md mb-4 text-sm font-medium border border-red-200">
						{authError}
					</div>
				{/if}

				<form onsubmit={handleAuth} class="flex flex-col gap-4">
					{#if !isLoginMode}
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
							<input type="text" bind:value={authUsername} required minlength="3" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" placeholder="scholar123" />
						</div>
					{/if}
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
						<input type="email" bind:value={authEmail} required class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" placeholder="you@example.com" />
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
						<input type="password" bind:value={authPassword} required minlength="6" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none" placeholder="••••••••" />
					</div>

					<button type="submit" disabled={isLoading} class="w-full bg-emerald-700 hover:bg-emerald-800 text-white p-3 rounded-lg font-bold transition shadow-md flex justify-center items-center gap-2 mt-2 disabled:bg-gray-400">
						{#if isLoading}
							<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
						{/if}
						{isLoginMode ? 'Sign In' : 'Register'}
					</button>
				</form>

				<div class="mt-6 text-center text-sm text-gray-600">
					{isLoginMode ? "Don't have an account?" : "Already have an account?"}
					<button type="button" onclick={() => { isLoginMode = !isLoginMode; authError = ''; }} class="text-emerald-700 font-bold hover:underline ml-1">
						{isLoginMode ? 'Sign up' : 'Log in'}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
