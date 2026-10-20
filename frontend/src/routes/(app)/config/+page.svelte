<script lang="ts">
	import { onMount } from 'svelte';

	let token = $state('');
	let activeTab = $state('books'); // 'books' | 'authors'

	// Entity Lists
	let books = $state<any[]>([]);
	let authors = $state<any[]>([]);
	let isLoading = $state(false);

	// Modals controls
	let showBookModal = $state(false);
	let showAuthorModal = $state(false);

	// Book Form State
	let bookTitle = $state('');
	let selectedAuthorId = $state('');
	let bookFile = $state<File | null>(null);
	let isCitationOnly = $state(false);
	let bookStatus = $state(''); // 'saving' | 'success' | 'error' | ''
	let bookError = $state('');

	// Author Form State
	let authorName = $state('');
	let authorEra = $state('');
	let authorBio = $state('');
	let authorStatus = $state(''); // 'saving' | 'success' | 'error' | ''
	let authorError = $state('');

	// Search & Pagination State
	const itemsPerPage = 10;
	
	let booksSearch = $state('');
	let booksPage = $state(1);
	
	let authorsSearch = $state('');
	let authorsPage = $state(1);

	// Reset page when search changes
	$effect(() => {
		booksSearch;
		booksPage = 1;
	});
	$effect(() => {
		authorsSearch;
		authorsPage = 1;
	});

	let filteredBooks = $derived(
		books.filter(b => 
			b.title.toLowerCase().includes(booksSearch.toLowerCase()) ||
			(b.author_name && b.author_name.toLowerCase().includes(booksSearch.toLowerCase()))
		)
	);

	let paginatedBooks = $derived(
		filteredBooks.slice((booksPage - 1) * itemsPerPage, booksPage * itemsPerPage)
	);

	let booksTotalPages = $derived(
		Math.max(1, Math.ceil(filteredBooks.length / itemsPerPage))
	);

	let filteredAuthors = $derived(
		authors.filter(a => 
			a.name.toLowerCase().includes(authorsSearch.toLowerCase()) ||
			(a.era && a.era.toLowerCase().includes(authorsSearch.toLowerCase())) ||
			(a.bio && a.bio.toLowerCase().includes(authorsSearch.toLowerCase()))
		)
	);

	let paginatedAuthors = $derived(
		filteredAuthors.slice((authorsPage - 1) * itemsPerPage, authorsPage * itemsPerPage)
	);

	let authorsTotalPages = $derived(
		Math.max(1, Math.ceil(filteredAuthors.length / itemsPerPage))
	);

	// AI settings state
	let aiMode = $state('local');
	let aiEndpoint = $state('http://localhost:11434');
	let aiModel = $state('llama3.1:8b');
	let aiWarnOnUse = $state(true);

	// App Language settings
	let appLanguage = $state('en');

	// Token Stats
	let tokenStats = $state<any>(null);
	let isLoadingStats = $state(false);

	async function fetchTokenStats() {
		isLoadingStats = true;
		try {
			const res = await fetch('http://localhost:8000/api/books/stats/tokens');
			if (res.ok) {
				tokenStats = await res.json();
			}
		} catch (err) {
			console.error('Error fetching token stats:', err);
		} finally {
			isLoadingStats = false;
		}
	}

	function formatNumber(n: number): string {
		if (!n && n !== 0) return '—';
		if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
		if (n >= 1_000) return (n / 1_000).toFixed(1) + 'k';
		return String(n);
	}

	onMount(async () => {
		token = localStorage.getItem('token') || '';
		if (!token) {
			window.location.href = '/';
			return;
		}
		
		// Fetch settings from storage
		aiMode = localStorage.getItem('aiMode') || 'local';
		aiEndpoint = localStorage.getItem('aiEndpoint') || 'http://localhost:11434';
		aiModel = localStorage.getItem('aiModel') || 'llama3.1:8b';
		aiWarnOnUse = localStorage.getItem('aiWarnOnUse') !== 'false';
		appLanguage = localStorage.getItem('appLanguage') || 'en';
		
		await loadData();
		await fetchTokenStats();
	});

	function saveSettings() {
		localStorage.setItem('aiMode', aiMode);
		localStorage.setItem('aiEndpoint', aiEndpoint);
		localStorage.setItem('aiModel', aiModel);
		localStorage.setItem('aiWarnOnUse', String(aiWarnOnUse));
		localStorage.setItem('appLanguage', appLanguage);
		alert("Settings saved successfully!");
		window.location.reload(); // Reload to apply language direction globally
	}

	async function loadData() {
		isLoading = true;
		try {
			const [booksRes, authorsRes] = await Promise.all([
				fetch('http://localhost:8000/api/books'),
				fetch('http://localhost:8000/api/authors')
			]);
			if (booksRes.ok) books = await booksRes.json();
			if (authorsRes.ok) authors = await authorsRes.json();
		} catch (err) {
			console.error("Error loading configuration data:", err);
		} finally {
			isLoading = false;
		}
	}

	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			bookFile = target.files[0];
		}
	}

	async function saveBook(e: Event) {
		e.preventDefault();
		if (!bookTitle.trim()) return;
		bookStatus = 'saving';
		bookError = '';

		try {
			const formData = new FormData();
			formData.append('title', bookTitle);
			if (selectedAuthorId) {
				formData.append('author_id', selectedAuthorId);
			}
			if (!isCitationOnly && bookFile) {
				formData.append('file', bookFile);
			}

			const res = await fetch('http://localhost:8000/api/books/upload', {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${token}`
				},
				body: formData
			});

			if (res.ok) {
				bookStatus = 'success';
				bookTitle = '';
				selectedAuthorId = '';
				bookFile = null;
				isCitationOnly = false;
				await loadData();
				setTimeout(() => {
					showBookModal = false;
					bookStatus = '';
				}, 1000);
			} else {
				const errData = await res.json();
				bookStatus = 'error';
				bookError = errData.detail || 'Failed to save book.';
			}
		} catch (err: any) {
			bookStatus = 'error';
			bookError = err.message || 'Network error occurred.';
		}
	}

	async function saveAuthor(e: Event) {
		e.preventDefault();
		if (!authorName.trim()) return;
		authorStatus = 'saving';
		authorError = '';

		try {
			const res = await fetch('http://localhost:8000/api/authors', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({
					name: authorName,
					era: authorEra,
					bio: authorBio
				})
			});

			if (res.ok) {
				authorStatus = 'success';
				authorName = '';
				authorEra = '';
				authorBio = '';
				await loadData();
				setTimeout(() => {
					showAuthorModal = false;
					authorStatus = '';
				}, 1000);
			} else {
				const errData = await res.json();
				authorStatus = 'error';
				authorError = errData.detail || 'Failed to save author.';
			}
		} catch (err: any) {
			authorStatus = 'error';
			authorError = err.message || 'Network error occurred.';
		}
	}
</script>

<svelte:head>
	<title>App Configuration - Islamic Notes</title>
</svelte:head>

<main class="flex-1 p-6 md:p-10 overflow-y-auto font-sans">
		<div class="flex justify-between items-center mb-6">
			<div>
				<h2 class="text-2xl md:text-3xl font-bold text-gray-800 mb-2">App Configuration</h2>
				<p class="text-gray-500">Manage reference library sources, downloaded books, and author indexes.</p>
			</div>
			
			<div class="flex gap-3">
				{#if activeTab === 'books'}
					<button onclick={() => showBookModal = true} class="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-4 py-2 rounded-lg transition shadow flex items-center gap-2 text-sm">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
						Add Book
					</button>
				{:else if activeTab === 'authors'}
					<button onclick={() => showAuthorModal = true} class="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-4 py-2 rounded-lg transition shadow flex items-center gap-2 text-sm">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
						Add Author
					</button>
				{/if}
			</div>
		</div>

		<!-- Tabs -->
		<div class="flex gap-4 border-b border-gray-200 mb-8">
			<button onclick={() => activeTab = 'books'} class="pb-3 px-2 font-bold text-sm transition-colors border-b-2 {activeTab === 'books' ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-800'}">Manage Books</button>
			<button onclick={() => activeTab = 'authors'} class="pb-3 px-2 font-bold text-sm transition-colors border-b-2 {activeTab === 'authors' ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-800'}">Manage Authors</button>
			<button onclick={() => activeTab = 'ai'} class="pb-3 px-2 font-bold text-sm transition-colors border-b-2 {activeTab === 'ai' ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-800'}">App & AI Settings</button>
		</div>

		{#if isLoading}
			<div class="flex justify-center p-12">
				<svg class="animate-spin h-8 w-8 text-emerald-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
			</div>
		{:else if activeTab === 'books'}
			<!-- Books Grid -->
			<div class="mb-4 flex max-w-xs">
				<input type="text" bind:value={booksSearch} placeholder="Search books..." class="w-full p-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-emerald-500" />
			</div>
			
			<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
				<table class="w-full text-left border-collapse">
					<thead>
						<tr class="bg-gray-50 border-b border-gray-200 text-xs font-bold text-gray-500 uppercase">
							<th class="p-4">Title</th>
							<th class="p-4">Linked Author</th>
							<th class="p-4">Type</th>
							<th class="p-4">File Path / Status</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100 text-sm">
						{#each paginatedBooks as book}
							<tr class="hover:bg-gray-50 transition">
								<td class="p-4 font-bold text-gray-900">{book.title}</td>
								<td class="p-4 text-gray-600">{book.author_name || 'Unspecified'}</td>
								<td class="p-4">
									<span class="px-2 py-0.5 rounded text-xs font-bold {book.file_path ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
										{book.file_path ? 'PDF Source' : 'Citation Only'}
									</span>
								</td>
								<td class="p-4 font-mono text-xs text-gray-400 max-w-xs truncate">{book.file_path || 'No local PDF'}</td>
							</tr>
						{:else}
							<tr>
								<td colspan="4" class="p-8 text-center text-gray-400">No books found.</td>
							</tr>
						{/each}
					</tbody>
				</table>

				<!-- Books Pagination Controls -->
				<div class="flex justify-between items-center p-4 border-t bg-gray-50 text-xs font-bold text-gray-500">
					<span>Showing {filteredBooks.length === 0 ? 0 : (booksPage - 1) * itemsPerPage + 1} - {Math.min(filteredBooks.length, booksPage * itemsPerPage)} of {filteredBooks.length}</span>
					<div class="flex gap-2 items-center">
						<button disabled={booksPage === 1} onclick={() => booksPage--} class="px-3 py-1.5 border rounded bg-white hover:bg-gray-100 disabled:opacity-50 transition">Previous</button>
						<span class="px-1">Page {booksPage} of {booksTotalPages}</span>
						<button disabled={booksPage === booksTotalPages} onclick={() => booksPage++} class="px-3 py-1.5 border rounded bg-white hover:bg-gray-100 disabled:opacity-50 transition">Next</button>
					</div>
				</div>
			</div>
		{:else if activeTab === 'authors'}
			<!-- Authors List -->
			<div class="mb-4 flex max-w-xs">
				<input type="text" bind:value={authorsSearch} placeholder="Search scholars/teachers..." class="w-full p-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-emerald-500" />
			</div>

			<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
				<table class="w-full text-left border-collapse">
					<thead>
						<tr class="bg-gray-50 border-b border-gray-200 text-xs font-bold text-gray-500 uppercase">
							<th class="p-4">Scholar Name</th>
							<th class="p-4">Era / Period</th>
							<th class="p-4">Bio / Notes</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100 text-sm">
						{#each paginatedAuthors as author}
							<tr class="hover:bg-gray-50 transition">
								<td class="p-4 font-bold text-gray-900">{author.name}</td>
								<td class="p-4 text-emerald-800 font-medium">{author.era || 'Unknown Period'}</td>
								<td class="p-4 text-gray-500 max-w-md truncate">{author.bio || 'No details provided.'}</td>
							</tr>
						{:else}
							<tr>
								<td colspan="3" class="p-8 text-center text-gray-400">No scholars found.</td>
							</tr>
						{/each}
					</tbody>
				</table>

				<!-- Authors Pagination Controls -->
				<div class="flex justify-between items-center p-4 border-t bg-gray-50 text-xs font-bold text-gray-500">
					<span>Showing {filteredAuthors.length === 0 ? 0 : (authorsPage - 1) * itemsPerPage + 1} - {Math.min(filteredAuthors.length, authorsPage * itemsPerPage)} of {filteredAuthors.length}</span>
					<div class="flex gap-2 items-center">
						<button disabled={authorsPage === 1} onclick={() => authorsPage--} class="px-3 py-1.5 border rounded bg-white hover:bg-gray-100 disabled:opacity-50 transition">Previous</button>
						<span class="px-1">Page {authorsPage} of {authorsTotalPages}</span>
						<button disabled={authorsPage === authorsTotalPages} onclick={() => authorsPage++} class="px-3 py-1.5 border rounded bg-white hover:bg-gray-100 disabled:opacity-50 transition">Next</button>
					</div>
				</div>
			</div>
		{:else if activeTab === 'ai'}
			<!-- AI Settings Grid -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
				<!-- Settings Card -->
				<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col gap-6">
					
					<h3 class="font-bold text-lg text-gray-900 border-b pb-2">App Layout Language</h3>
					<div>
						<label class="block text-xs font-bold text-gray-500 uppercase mb-2">Display Language</label>
						<select bind:value={appLanguage} class="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none bg-white">
							<option value="en">English (Left to Right)</option>
							<option value="id">Bahasa Indonesia (Left to Right)</option>
							<option value="ar">العربية (Right to Left)</option>
						</select>
						<p class="text-xs text-gray-400 mt-1">Changes layout direction and UI text language where applicable.</p>
					</div>

					<h3 class="font-bold text-lg text-gray-900 border-b pb-2 mt-2">AI Deployment Mode</h3>
					
					<div>
						<label class="block text-xs font-bold text-gray-500 uppercase mb-2">AI Deployment Strategy</label>
						<div class="flex flex-col gap-2">
							<label class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
								<input type="radio" bind:group={aiMode} value="local" class="text-emerald-600 focus:ring-emerald-500" />
								Deploy AI Locally (Ollama / Llama.cpp)
							</label>
							<label class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
								<input type="radio" bind:group={aiMode} value="online" class="text-emerald-600 focus:ring-emerald-500" />
								Use Online Model (Gemini Pro Cloud API)
							</label>
						</div>
					</div>

					{#if aiMode === 'local'}
						<div>
							<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Ollama Connection Endpoint</label>
							<input type="text" bind:value={aiEndpoint} placeholder="http://localhost:11434" class="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none" />
						</div>
						<div>
							<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Local Model Tag</label>
							<input type="text" bind:value={aiModel} placeholder="llama3.1:8b" class="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none" />
						</div>
					{:else}
						<div>
							<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Cloud Gemini API Key</label>
							<input type="password" placeholder="••••••••••••••••••••••••" class="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none" />
							<p class="text-xs text-gray-400 mt-1">Saves key securely in local environment.</p>
						</div>
					{/if}

					<div class="flex items-center gap-2 border-t pt-4">
						<input type="checkbox" id="warn_ai" bind:checked={aiWarnOnUse} class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
						<label for="warn_ai" class="text-sm font-semibold text-gray-700 select-none cursor-pointer">Show Warning Banner before using AI features</label>
					</div>

					<button onclick={saveSettings} class="bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-2 px-4 rounded-lg text-sm transition shadow mt-4 self-end">
						Save Settings
					</button>
				</div>

				<!-- Stats Card -->
				<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
					<div class="flex justify-between items-center border-b pb-2 mb-4">
						<h3 class="font-bold text-lg text-gray-900">Library & Workspace Statistics</h3>
						<button onclick={fetchTokenStats} title="Refresh stats" class="text-gray-400 hover:text-emerald-700 transition">
							<svg class="w-4 h-4 {isLoadingStats ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
						</button>
					</div>
					
					{#if isLoadingStats}
						<div class="flex justify-center py-8">
							<svg class="animate-spin h-6 w-6 text-emerald-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
						</div>
					{:else}
						<div class="grid grid-cols-2 gap-4">
							<div class="p-4 bg-gray-50 rounded-lg">
								<div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Total Books</div>
								<div class="text-2xl font-extrabold text-emerald-800">{tokenStats ? tokenStats.total_books : '—'}</div>
							</div>
							<div class="p-4 bg-gray-50 rounded-lg">
								<div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Total Scholars</div>
								<div class="text-2xl font-extrabold text-emerald-800">{tokenStats ? tokenStats.total_authors : '—'}</div>
							</div>
							<div class="p-4 bg-gray-50 rounded-lg">
								<div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Notes (est. tokens)</div>
								<div class="text-2xl font-extrabold text-emerald-800">{tokenStats ? formatNumber(tokenStats.notes_tokens) : '—'}</div>
								<div class="text-xs text-gray-400 mt-1">from your commits</div>
							</div>
							<div class="p-4 bg-gray-50 rounded-lg">
								<div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Total Est. Tokens</div>
								<div class="text-2xl font-extrabold text-emerald-800">{tokenStats ? formatNumber(tokenStats.total_tokens) : '—'}</div>
								<div class="text-xs text-gray-400 mt-1">~4 chars per token</div>
							</div>
						</div>

						{#if tokenStats && tokenStats.total_books === 0}
							<div class="mt-4 p-3 bg-amber-50 border border-amber-100 rounded-lg text-xs text-amber-800">
								<strong>No books yet.</strong> Go to <a href="/config" class="underline font-bold">Manage Books</a> tab to upload your first PDF or add a citation reference.
							</div>
						{/if}
					{/if}

					<div class="mt-6 p-4 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-800 flex gap-2">
						<svg class="w-5 h-5 shrink-0 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
						<p><strong>Cost Savings Tip:</strong> Running your AI model locally (e.g. using Ollama) requires zero external network calls, offloads computation to your local GPU, and does not incur any SaaS subscription fees.</p>
					</div>
				</div>
			</div>
		{/if}
	</main>
<!-- Modal: Add Book -->
{#if showBookModal}
	<div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
		<div class="bg-white w-full max-w-md rounded-xl shadow-2xl p-6 relative">
			<button onclick={() => showBookModal = false} class="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition">
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
			</button>

			<h3 class="font-bold text-xl text-gray-900 mb-4">Register New Book</h3>

			{#if bookError}
				<div class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-xs mb-4">{bookError}</div>
			{/if}

			<form onsubmit={saveBook} class="flex flex-col gap-4">
				<div>
					<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Book Title</label>
					<input type="text" bind:value={bookTitle} required placeholder="e.g. Al-Wajiz fi Fiqh As-Sunnah" class="w-full p-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 text-sm" />
				</div>

				<div>
					<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Author / Scholar</label>
					<select bind:value={selectedAuthorId} class="w-full p-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 text-sm bg-white">
						<option value="">-- No linked author --</option>
						{#each authors as author}
							<option value={author.id}>{author.name} ({author.era || 'N/A'})</option>
						{/each}
					</select>
				</div>

				<div class="flex items-center gap-2 my-1">
					<input type="checkbox" id="citation_only" bind:checked={isCitationOnly} class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
					<label for="citation_only" class="text-sm text-gray-700 select-none">Citation source only (No PDF upload)</label>
				</div>

				{#if !isCitationOnly}
					<div class="p-4 border-2 border-dashed border-gray-200 rounded-lg text-center hover:bg-gray-50 transition relative">
						<input type="file" accept=".pdf" onchange={handleFileSelect} class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
						<svg class="mx-auto h-8 w-8 text-gray-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
						{#if bookFile}
							<p class="text-xs font-bold text-emerald-600 truncate">{bookFile.name}</p>
						{:else}
							<p class="text-xs text-gray-600 font-medium">Click to select PDF book file</p>
						{/if}
					</div>
				{/if}

				<div class="flex justify-end gap-2 mt-2">
					<button type="button" onclick={() => showBookModal = false} class="px-4 py-2 border rounded-lg hover:bg-gray-50 text-sm font-semibold transition">Cancel</button>
					<button type="submit" disabled={bookStatus === 'saving'} class="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-sm font-semibold transition disabled:bg-gray-400">
						{bookStatus === 'saving' ? 'Saving...' : 'Register Book'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- Modal: Add Author -->
{#if showAuthorModal}
	<div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
		<div class="bg-white w-full max-w-md rounded-xl shadow-2xl p-6 relative">
			<button onclick={() => showAuthorModal = false} class="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition">
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
			</button>

			<h3 class="font-bold text-xl text-gray-900 mb-4">Add Scholar / Author</h3>

			{#if authorError}
				<div class="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-xs mb-4">{authorError}</div>
			{/if}

			<form onsubmit={saveAuthor} class="flex flex-col gap-4">
				<div>
					<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Scholar Name</label>
					<input type="text" bind:value={authorName} required placeholder="e.g. Imam al-Nawawi" class="w-full p-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 text-sm" />
				</div>

				<div>
					<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Era / Period</label>
					<input type="text" bind:value={authorEra} placeholder="e.g. 631-676 AH or Modern" class="w-full p-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 text-sm" />
				</div>

				<div>
					<label class="block text-xs font-bold text-gray-500 uppercase mb-1">Biography / Info</label>
					<textarea bind:value={authorBio} rows="4" placeholder="Brief details about the teacher or author..." class="w-full p-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 text-sm"></textarea>
				</div>

				<div class="flex justify-end gap-2 mt-2">
					<button type="button" onclick={() => showAuthorModal = false} class="px-4 py-2 border rounded-lg hover:bg-gray-50 text-sm font-semibold transition">Cancel</button>
					<button type="submit" disabled={authorStatus === 'saving'} class="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-sm font-semibold transition disabled:bg-gray-400">
						{authorStatus === 'saving' ? 'Saving...' : 'Add Scholar'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.animate-fade-in {
		animation: fadeIn 0.2s ease-out forwards;
	}
	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(5px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
