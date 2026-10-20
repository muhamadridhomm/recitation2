<script lang="ts">
	import { onMount } from 'svelte';

	let isLoggedIn = $state(false);
	let token = $state('');
	let books = $state<any[]>([]);
	let authors = $state<any[]>([]);
	let searchQuery = $state('');
	let isLoading = $state(true);

	// Pagination
	const PAGE_SIZE = 12;
	let currentPage = $state(1);

	// Reset page on search
	$effect(() => {
		searchQuery;
		currentPage = 1;
	});

	// Create project modal
	let showCreateModal = $state(false);
	let selectedBook = $state<any>(null);
	let projectTitle = $state('');
	let projectDesc = $state('');
	let selectedTeacherId = $state('');
	let createStatus = $state('');

	onMount(async () => {
		token = localStorage.getItem('token') || '';
		if (token) isLoggedIn = true;
		await Promise.all([fetchBooks(), fetchAuthors()]);
		isLoading = false;
	});

	async function fetchBooks() {
		try {
			const res = await fetch('http://localhost:8000/api/books');
			if (res.ok) books = await res.json();
		} catch (err) {
			console.error('Error fetching books:', err);
		}
	}

	async function fetchAuthors() {
		try {
			const res = await fetch('http://localhost:8000/api/authors');
			if (res.ok) authors = await res.json();
		} catch (err) {
			console.error('Error fetching authors:', err);
		}
	}

	// ── "Read Now" — open PDF directly in reader without a project ──
	function readNow(book: any) {
		if (!book.file_path) {
			alert('This entry is citation-only and has no PDF to open.');
			return;
		}
		// Pass book_id so the reader can load the file
		window.location.href = `/reader?book_id=${book.id}`;
	}

	// ── "Start Study Project" ──
	function openCreateModal(book: any) {
		if (!isLoggedIn) {
			alert('Please log in to create a study project.');
			return;
		}
		selectedBook = book;
		projectTitle = `Study of ${book.title}`;
		projectDesc = `My study notes and highlights on ${book.title} by ${book.author_name || 'Classical Scholar'}`;
		selectedTeacherId = book.author_id || '';
		createStatus = '';
		showCreateModal = true;
	}

	async function createProject(e: Event) {
		e.preventDefault();
		if (!projectTitle.trim() || !selectedBook) return;
		createStatus = 'creating';
		try {
			const res = await fetch('http://localhost:8000/api/projects', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({
					title: projectTitle,
					description: projectDesc,
					document_id: selectedBook.id,
					teacher_id: selectedTeacherId || null
				})
			});
			if (res.ok) {
				const project = await res.json();
				createStatus = 'success';
				setTimeout(() => {
					window.location.href = `/reader?project_id=${project.id}`;
				}, 500);
			} else {
				alert('Failed to create study project.');
				createStatus = '';
			}
		} catch (err) {
			console.error(err);
			alert('Error creating project.');
			createStatus = '';
		}
	}

	// ── Derived state ──
	let filteredBooks = $derived(
		books.filter(b =>
			b.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
			(b.author_name && b.author_name.toLowerCase().includes(searchQuery.toLowerCase()))
		)
	);

	let totalPages = $derived(Math.max(1, Math.ceil(filteredBooks.length / PAGE_SIZE)));

	let paginatedBooks = $derived(
		filteredBooks.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
	);

	// Visible page numbers (max 5 around current)
	let pageNumbers = $derived(() => {
		const pages: number[] = [];
		const delta = 2;
		const left = Math.max(1, currentPage - delta);
		const right = Math.min(totalPages, currentPage + delta);
		for (let i = left; i <= right; i++) pages.push(i);
		return pages;
	});
</script>

<svelte:head>
	<title>Books Library - Islamic Notes</title>
	<meta name="description" content="Browse, read, and study books from the Islamic Notes library. Open PDFs directly or create a study project with notes and highlights." />
</svelte:head>

<main class="flex-1 px-6 py-8 max-w-7xl mx-auto w-full overflow-auto">

			<!-- Header row -->
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
			<div>
				<h1 class="text-3xl font-bold text-gray-900 mb-1">Books Library</h1>
				<p class="text-gray-500 text-sm">
					{#if isLoading}
						Loading…
					{:else}
						{filteredBooks.length} book{filteredBooks.length !== 1 ? 's' : ''} available
						{#if searchQuery} matching "<span class="font-semibold text-emerald-700">{searchQuery}</span>"{/if}
					{/if}
				</p>
			</div>
			<!-- Search -->
			<div class="relative">
				<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"></path></svg>
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search by title or author…"
					class="pl-9 pr-4 py-2.5 border border-gray-300 rounded-xl outline-none focus:ring-2 focus:ring-emerald-500 text-sm w-72 bg-white shadow-sm"
				/>
			</div>
		</div>

		{#if isLoading}
			<!-- Skeleton loader -->
			<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
				{#each Array(8) as _}
					<div class="bg-white rounded-xl border border-gray-200 overflow-hidden animate-pulse">
						<div class="h-40 bg-gray-200"></div>
						<div class="p-4 space-y-2">
							<div class="h-3 bg-gray-200 rounded w-1/3"></div>
							<div class="h-4 bg-gray-200 rounded w-3/4"></div>
							<div class="h-3 bg-gray-200 rounded w-1/2"></div>
						</div>
					</div>
				{/each}
			</div>
		{:else if filteredBooks.length === 0}
			<div class="flex flex-col items-center justify-center py-24 text-gray-400">
				<svg class="w-16 h-16 mb-4 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
				{#if searchQuery}
					<p class="text-lg font-semibold">No books found for "{searchQuery}"</p>
					<button onclick={() => searchQuery = ''} class="mt-3 text-sm text-emerald-600 hover:underline">Clear search</button>
				{:else}
					<p class="text-lg font-semibold">Library is empty</p>
					<p class="text-sm mt-1">Upload books from the <a href="/config" class="text-emerald-600 hover:underline font-semibold">App Config</a> page.</p>
				{/if}
			</div>
		{:else}
			<!-- Book Grid -->
			<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-8">
				{#each paginatedBooks as book (book.id)}
					<div class="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-lg hover:border-emerald-200 transition-all duration-200 group overflow-hidden flex flex-col">

						<!-- Thumbnail area -->
						<div class="h-48 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center border-b border-gray-100 relative overflow-hidden">
							{#if book.file_path}
								<img src={`http://localhost:8000/api/books/${book.id}/thumbnail`} alt={book.title} class="w-full h-full object-cover" onerror={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextElementSibling.style.display = 'block'; }} />
								<!-- Fallback icon if image fails to load -->
								<svg class="w-16 h-16 text-gray-300 hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
								</svg>
							{:else}
								<!-- Big decorative icon for Citation books -->
								<svg class="w-16 h-16 text-emerald-200 group-hover:text-emerald-300 transition-colors duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
								</svg>
							{/if}

							<!-- Type badge top-left -->
							<span class="absolute top-2 left-2 text-xs font-bold px-2 py-0.5 rounded-full {book.file_path ? 'bg-emerald-600 text-white' : 'bg-amber-100 text-amber-700 border border-amber-200'}">
								{book.file_path ? 'PDF' : 'Citation'}
							</span>

							<!-- Hover action overlay -->
							<div class="absolute inset-0 bg-gray-900/70 backdrop-blur-sm flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-3">
								{#if book.file_path}
									<!-- svelte-ignore a11y_consider_explicit_label -->
									<button
										onclick={() => readNow(book)}
										class="w-full bg-white hover:bg-emerald-50 text-emerald-800 font-bold text-xs py-2 px-3 rounded-lg flex items-center justify-center gap-1.5 transition shadow"
									>
										<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
										Read Now
									</button>
								{/if}
								<button
									onclick={() => openCreateModal(book)}
									class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-2 px-3 rounded-lg flex items-center justify-center gap-1.5 transition shadow"
								>
									<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
									Start Study Project
								</button>
							</div>
						</div>

						<!-- Card body -->
						<div class="p-4 flex-1 flex flex-col">
							<h3 class="font-bold text-gray-900 text-sm leading-snug line-clamp-2 mb-1">{book.title}</h3>
							<p class="text-xs text-gray-500 truncate">{book.author_name || 'Unknown Author'}</p>
							<div class="mt-auto pt-3 border-t border-gray-100 flex justify-between items-center">
								<span class="text-xs text-gray-400">{new Date(book.created_at || Date.now()).toLocaleDateString('en-US', { month:'short', year:'numeric' })}</span>
								{#if book.file_path}
									<!-- svelte-ignore a11y_consider_explicit_label -->
									<button
										onclick={() => readNow(book)}
										class="text-xs font-bold text-emerald-700 hover:text-emerald-900 hover:underline transition flex items-center gap-0.5"
									>
										Read
										<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"></path></svg>
									</button>
								{:else}
									<span class="text-xs text-amber-600 font-bold">Ref only</span>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>

			<!-- Pagination -->
			{#if totalPages > 1}
				<div class="flex items-center justify-between border-t border-gray-200 pt-6">
					<p class="text-sm text-gray-500">
						Showing <span class="font-semibold text-gray-800">{(currentPage - 1) * PAGE_SIZE + 1}–{Math.min(filteredBooks.length, currentPage * PAGE_SIZE)}</span>
						of <span class="font-semibold text-gray-800">{filteredBooks.length}</span> books
					</p>

					<nav class="flex items-center gap-1" aria-label="Pagination">
						<!-- First -->
						<button
							disabled={currentPage === 1}
							onclick={() => currentPage = 1}
							class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
							title="First page"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"></path></svg>
						</button>

						<!-- Prev -->
						<button
							disabled={currentPage === 1}
							onclick={() => currentPage--}
							class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
							title="Previous page"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
						</button>

						<!-- Page numbers -->
						{#each pageNumbers() as pg}
							<button
								onclick={() => currentPage = pg}
								class="w-9 h-9 rounded-lg border text-sm font-bold transition
									{pg === currentPage
										? 'bg-emerald-700 text-white border-emerald-700 shadow-sm'
										: 'border-gray-200 text-gray-600 hover:bg-gray-50'}"
							>
								{pg}
							</button>
						{/each}

						<!-- Next -->
						<button
							disabled={currentPage === totalPages}
							onclick={() => currentPage++}
							class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
							title="Next page"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
						</button>

						<!-- Last -->
						<button
							disabled={currentPage === totalPages}
							onclick={() => currentPage = totalPages}
							class="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
							title="Last page"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>
						</button>
					</nav>
				</div>
			{/if}
		{/if}
	</main>

<!-- Modal: Create Study Project -->
{#if showCreateModal && selectedBook}
	<div class="fixed inset-0 bg-gray-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
		<div class="bg-white w-full max-w-md rounded-2xl shadow-2xl p-6 relative animate-modal">
			<button onclick={() => showCreateModal = false} class="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition">
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
			</button>

			<!-- Book preview in modal -->
			<div class="flex items-center gap-3 mb-5 p-3 bg-emerald-50 rounded-xl border border-emerald-100">
				<div class="w-10 h-10 bg-emerald-600 text-white rounded-lg flex items-center justify-center shrink-0">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
				</div>
				<div class="min-w-0">
					<p class="font-bold text-emerald-900 text-sm truncate">{selectedBook.title}</p>
					<p class="text-xs text-emerald-700">{selectedBook.author_name || 'Unknown Author'}</p>
				</div>
			</div>

			<h3 class="font-bold text-xl text-gray-900 mb-1">Start a Study Project</h3>
			<p class="text-xs text-gray-500 mb-5">A project lets you add notes, highlights, and bookmarks on top of this book.</p>

			{#if createStatus === 'success'}
				<div class="flex items-center gap-2 p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-sm font-semibold">
					<svg class="w-5 h-5 shrink-0 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
					Project created! Opening reader…
				</div>
			{:else}
				<form onsubmit={createProject} class="flex flex-col gap-4">
					<div>
						<label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Project Title</label>
						<input type="text" bind:value={projectTitle} required class="w-full p-2.5 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 text-sm font-semibold" />
					</div>

					<div>
						<label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Description</label>
						<textarea bind:value={projectDesc} rows="2" class="w-full p-2.5 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 text-sm resize-none"></textarea>
					</div>

					<div>
						<label class="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Ustadz / Teacher</label>
						<select bind:value={selectedTeacherId} class="w-full p-2.5 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500 text-sm bg-white">
							<option value="">-- No specific teacher --</option>
							{#each authors as author}
								<option value={author.id}>{author.name}</option>
							{/each}
						</select>
					</div>

					<div class="flex justify-end gap-2 mt-1">
						<button type="button" onclick={() => showCreateModal = false} class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm font-semibold transition text-gray-700">Cancel</button>
						<button type="submit" disabled={createStatus === 'creating'} class="px-5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-sm font-bold transition shadow disabled:bg-gray-400 flex items-center gap-1.5">
							{#if createStatus === 'creating'}
								<svg class="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
								Creating…
							{:else}
								Start Studying
							{/if}
						</button>
					</div>
				</form>
			{/if}
		</div>
	</div>
{/if}

<style>
	@keyframes modalIn {
		from { opacity: 0; transform: scale(0.96) translateY(8px); }
		to   { opacity: 1; transform: scale(1) translateY(0); }
	}
	.animate-modal {
		animation: modalIn 0.18s ease-out forwards;
	}
</style>
