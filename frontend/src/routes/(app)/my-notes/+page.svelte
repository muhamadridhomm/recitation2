<script lang="ts">
	import { onMount } from 'svelte';
	import { appState } from '$lib/store.svelte';

	let token = $state('');
	let projects = $state<any[]>([]);
	let authors = $state<any[]>([]);
	let localBooks = $state<any[]>([]);
	let showNewProjectModal = $state(false);
	let newProjectName = $state('');
	let selectedBookId = $state('default-doc');
	let selectedTeacherId = $state('');
	let isThematic = $state(false);
	let aiSearchQuery = $state('');
	let isAiSearching = $state(false);
	let aiSearchResults = $state<any[]>([]);
	let hasSearchedAi = $state(false);

	// Book source mode: 'library' | 'ai'
	let bookSourceTab = $state<'library' | 'ai'>('library');
	let librarySearch = $state('');
	let selectedLibraryBook = $state<any>(null);

	let isRtl = $derived(appState.language === 'ar');

	onMount(async () => {
		appState.language = localStorage.getItem('appLanguage') || 'en';
		const storedToken = localStorage.getItem('token');
		if (!storedToken) {
			window.location.href = '/';
			return;
		}
		token = storedToken;
		await fetchProjects();
		await fetchAuthors();
		await fetchLocalBooks();
	});

	async function fetchProjects() {
		try {
			const res = await fetch('http://localhost:8000/api/projects', {
				headers: {
					'Authorization': `Bearer ${token}`
				}
			});
			if (res.ok) {
				projects = await res.json();
			}
		} catch (err) {
			console.error('Error fetching projects:', err);
		}
	}

	async function fetchAuthors() {
		try {
			const res = await fetch('http://localhost:8000/api/authors');
			if (res.ok) {
				authors = await res.json();
			}
		} catch (err) {
			console.error('Error fetching authors:', err);
		}
	}

	async function fetchLocalBooks() {
		try {
			const res = await fetch('http://localhost:8000/api/books');
			if (res.ok) {
				localBooks = await res.json();
			}
		} catch (err) {
			console.error('Error fetching local books:', err);
		}
	}

	async function createProject(bookId: string | null) {
		if (!newProjectName.trim()) return;
		try {
			const res = await fetch('http://localhost:8000/api/projects', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`
				},
				body: JSON.stringify({
					title: newProjectName,
					document_id: isThematic ? null : bookId,
					teacher_id: selectedTeacherId || null
				})
			});
			if (res.ok) {
				showNewProjectModal = false;
				newProjectName = '';
				selectedTeacherId = '';
				isThematic = false;
				hasSearchedAi = false;
				aiSearchResults = [];
				selectedLibraryBook = null;
				librarySearch = '';
				bookSourceTab = 'library';
				await fetchProjects();
			}
		} catch (err) {
			console.error('Error creating project:', err);
		}
	}


	let showAiWarningModal = $state(false);
	let dontWarnAgain = $state(false);

	function triggerAiSearch() {
		const warn = localStorage.getItem('aiWarnOnUse') !== 'false';
		if (warn) {
			showAiWarningModal = true;
		} else {
			handleAiSearch();
		}
	}

	function confirmAiSearch() {
		if (dontWarnAgain) {
			localStorage.setItem('aiWarnOnUse', 'false');
		}
		showAiWarningModal = false;
		handleAiSearch();
	}

	function handleAiSearch() {
		if (!aiSearchQuery.trim()) return;
		isAiSearching = true;
		hasSearchedAi = true;
		
		// 1. Search local books first
		const matches = localBooks.filter(b => 
			b.title.toLowerCase().includes(aiSearchQuery.toLowerCase()) ||
			(b.author_name && b.author_name.toLowerCase().includes(aiSearchQuery.toLowerCase()))
		);

		// Format matches for search result displays
		const localResults = matches.map(b => ({
			id: b.id,
			title: b.title,
			source: 'Local Books Library',
			status: b.file_path ? 'Downloaded' : 'Citation Only'
		}));

		setTimeout(() => {
			if (localResults.length > 0) {
				aiSearchResults = localResults;
			} else {
				// Fallback to simulated online searches
				if (aiSearchQuery.includes('bukhari') || aiSearchQuery.includes('بخاري')) {
					aiSearchResults = [
						{ id: 'bukhari-1', title: 'Sahih al-Bukhari (Dar Ibn Kathir)', source: 'Maktaba Shamela (Online)', status: 'Available' },
					];
				} else {
					aiSearchResults = [
						{ id: 'custom-book', title: `Create custom online entry for: ${aiSearchQuery}`, source: 'Maktaba Waqfeya (Online)', status: 'Available' }
					];
				}
			}
			isAiSearching = false;
		}, 600);
	}

	// Derived filtered library books for modal search
	let filteredLibraryBooks = $derived(
		librarySearch.trim() === ''
			? localBooks
			: localBooks.filter(b =>
					b.title.toLowerCase().includes(librarySearch.toLowerCase()) ||
					(b.author_name && b.author_name.toLowerCase().includes(librarySearch.toLowerCase()))
				)
	);
</script>

<svelte:head>
	<title>My Notes - Dashboard</title>
</svelte:head>

<!-- Flip the entire dashboard layout (including sidebar) based on global language -->
<div class="flex-1 p-6 md:p-10 font-sans" dir={isRtl ? 'rtl' : 'ltr'}>
		<div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 gap-4">
			<h2 class="text-2xl md:text-3xl font-bold text-gray-800">My Note Projects</h2>
			<button onclick={() => showNewProjectModal = true} class="bg-emerald-700 hover:bg-emerald-800 text-white px-6 py-3 rounded-lg font-bold transition shadow-md flex items-center gap-2">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
				New Project
			</button>
		</div>

		<!-- Projects Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each projects as project}
				<div
					class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition cursor-pointer group"
					dir={isRtl ? 'rtl' : 'ltr'}
				>
					<div class="flex justify-between items-start mb-4">
						<div class="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-700 shrink-0">
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
						</div>
						<a
							href="/reader?project_id={project.id}"
							class="opacity-0 group-hover:opacity-100 text-sm text-blue-600 hover:underline transition flex items-center gap-1"
							dir="ltr"
						>
							Open Reader
							<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
						</a>
					</div>
					<h3 class="font-bold text-lg text-gray-900 mb-1 leading-snug">{project.title}</h3>
					{#if project.document_id}
						<p class="text-sm text-gray-500 mb-1 truncate">{project.document_id}</p>
					{:else}
						<p class="text-sm text-indigo-600 font-semibold mb-1">Thematic Notes (Multi-source)</p>
					{/if}
					
					{#if project.teacher_name}
						<p class="text-xs text-emerald-700 font-bold mb-4">Teacher: Ust. {project.teacher_name}</p>
					{:else}
						<p class="text-xs text-gray-400 mb-4">No teacher assigned</p>
					{/if}
					
					<div class="flex justify-between items-center text-xs text-gray-400 border-t pt-4">
						<span>Created {new Date(project.created_at).toLocaleDateString()}</span>
						{#if project.forked_from_id}
							<span class="text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full font-bold">Fork</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>
</div>
