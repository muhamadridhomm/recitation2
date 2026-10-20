<script lang="ts">
	import { onMount } from 'svelte';
	import { appState } from '$lib/store.svelte';

	let searchQuery = $state('');
	let isSearching = $state(false);
	let hasSearched = $state(false);
	
	let direction = $derived(appState.language === 'ar' ? 'rtl' : 'ltr');
	
	let isLoggedIn = $state(false);
	let token = $state('');

	// Personalized search state
	let searchMode = $state('global'); // 'global' | 'workspace'
	let books = $state<any[]>([]);
	let userProjects = $state<any[]>([]);

	onMount(async () => {
		token = localStorage.getItem('token') || '';
		if (token) {
			isLoggedIn = true;
			await fetchUserProjects();
		}
		await fetchBooks();
	});

	async function fetchBooks() {
		try {
			const res = await fetch('http://localhost:8000/api/books');
			if (res.ok) {
				books = await res.json();
			}
		} catch (err) {
			console.error("Error fetching books:", err);
		}
	}

	async function fetchUserProjects() {
		try {
			const res = await fetch('http://localhost:8000/api/projects?public=false', {
				headers: {
					'Authorization': `Bearer ${token}`
				}
			});
			if (res.ok) {
				userProjects = await res.json();
			}
		} catch (err) {
			console.error("Error fetching workspace projects:", err);
		}
	}

	function handleLogout() {
		localStorage.removeItem('token');
		isLoggedIn = false;
		searchMode = 'global';
		userProjects = [];
	}

	const dict = {
		en: {
			logo: "Search Engine",
			quran: "Al-Qur'an",
			hadith: "Hadith",
			duas: "Du'as",
			notes: "Public Notes",
			books: "Books Library",
			authors: "Authors",
			login: "Login",
			start: "Start Noting",
			hero1: "Search Islamic ",
			hero2: "Knowledge",
			sub: "Search millions of pages, public notes, and classical texts.",
			placeholder: "Search for tafsir, hadith, or fiqh rules...",
			results: "About 115,000 results (0.42 seconds)"
		},
		ar: {
			logo: "محرك البحث",
			quran: "القرآن",
			hadith: "الحديث",
			duas: "الأدعية",
			notes: "الملاحظات العامة",
			books: "مكتبة الكتب",
			authors: "المؤلفون",
			login: "تسجيل الدخول",
			start: "ابدأ التدوين",
			hero1: "ابحث في المعرفة ",
			hero2: "الإسلامية",
			sub: "ابحث في ملايين الصفحات، والملاحظات العامة، والنصوص الكلاسيكية.",
			placeholder: "ابحث عن تفسير، حديث، أو قاعدة فقهية...",
			results: "حوالي 115,000 نتيجة (0.42 ثانية)"
		},
		id: {
			logo: "Mesin Pencari",
			quran: "Al-Qur'an",
			hadith: "Hadits",
			duas: "Do'a",
			notes: "Catatan Publik",
			books: "Perpustakaan Buku",
			authors: "Penulis",
			login: "Masuk",
			start: "Mulai Mencatat",
			hero1: "Cari Pengetahuan ",
			hero2: "Islam",
			sub: "Cari jutaan halaman, catatan publik, dan teks klasik.",
			placeholder: "Cari tafsir, hadits, atau aturan fiqih...",
			results: "Sekitar 115.000 hasil (0,42 detik)"
		}
	};
	let t = $derived(dict[appState.language as keyof typeof dict]);

	// Mock semantic search results
	let mockResults = [
		{ id: 1, title: 'Al-Risalah', author: 'Imam Shafi’i', type: 'Book', context: '...فإن القرآن نزل بلغة العرب، ولا يعلم <b>تفسيره</b> إلا من علم لغتها...', tags: ['Usul al-Fiqh'] },
		{ id: 2, title: 'Note: On Patience in Trials', author: 'User_IbnSina', type: 'Public Note', context: '...this hadith highlights the importance of <b>صبر</b> (patience) when facing hardship...', tags: ['Akhlaq', 'Hadith'] },
		{ id: 3, title: 'Sahih Muslim', author: 'Muslim ibn al-Hajjaj', type: 'Book', context: '...عن أبي هريرة قال: قال رسول الله صلى الله عليه وسلم: <b>الدين النصيحة</b>...', tags: ['Hadith'] }
	];

	// Filtered items based on search query
	let filteredBooks = $derived(
		searchQuery.trim()
			? books.filter(b => 
				b.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(b.author_name && b.author_name.toLowerCase().includes(searchQuery.toLowerCase()))
			)
			: []
	);

	let filteredProjects = $derived(
		searchQuery.trim()
			? userProjects.filter(p => 
				p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
				(p.teacher_name && p.teacher_name.toLowerCase().includes(searchQuery.toLowerCase()))
			)
			: []
	);

	function handleSearch() {
		if (!searchQuery.trim()) {
			hasSearched = false;
			return;
		}
		isSearching = true;
		
		setTimeout(() => {
			hasSearched = true;
			isSearching = false;
		}, 400);
	}

</script>

<svelte:head>
	<title>Arabic Document Intelligence - Search</title>
</svelte:head>
	<!-- Main Search Area -->
	<main class="flex-1 flex flex-col items-center pt-20 px-6" dir={direction}>
		<div class="w-full max-w-3xl flex flex-col items-center transition-all duration-500 {hasSearched ? '-translate-y-10' : ''}">
			<!-- Logo Area -->
			<div class="mb-8 text-center">
				<h1 class="text-5xl font-extrabold text-gray-900 mb-4 tracking-tight">{t.hero1} <span class="text-emerald-600">{t.hero2}</span></h1>
				<p class="text-lg text-gray-500">{t.sub}</p>
			</div>

			<!-- Logged-in Personalized Tab Switcher -->
			{#if isLoggedIn}
				<div class="flex bg-gray-100 p-1 rounded-lg gap-2 mb-6 border border-gray-200">
					<button 
						onclick={() => { searchMode = 'global'; hasSearched = false; }} 
						class="px-4 py-1.5 rounded-md text-sm font-bold transition-all {searchMode === 'global' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-800'}"
					>
						Global Library Search
					</button>
					<button 
						onclick={() => { searchMode = 'workspace'; hasSearched = false; }} 
						class="px-4 py-1.5 rounded-md text-sm font-bold transition-all {searchMode === 'workspace' ? 'bg-white text-emerald-800 shadow-sm' : 'text-gray-500 hover:text-gray-800'}"
					>
						My Workspace Notes
					</button>
				</div>
			{/if}

			<!-- Search Bar -->
			<div class="w-full relative shadow-lg rounded-full group hover:shadow-xl transition-shadow">
				<div class="absolute inset-y-0 right-0 flex items-center pr-6 pointer-events-none" class:right-0={direction === 'rtl'} class:left-0={direction === 'ltr'}>
					<svg class="w-5 h-5 text-gray-400 group-hover:text-emerald-500 transition {direction === 'ltr' ? 'ml-6' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
				</div>
				<input 
					type="text" 
					bind:value={searchQuery} 
					onkeypress={(e) => e.key === 'Enter' && handleSearch()}
					placeholder={searchMode === 'workspace' ? 'Search study projects, teachers, descriptions...' : t.placeholder}
					class="w-full py-4 text-lg border border-gray-200 rounded-full focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all {direction === 'rtl' ? 'pr-14 pl-6' : 'pl-14 pr-6'}"
				>
			</div>

			<!-- Loader -->
			{#if isSearching}
				<div class="mt-8 text-emerald-600">
					<svg class="animate-spin h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
				</div>
			{/if}
		</div>

		<!-- Search Results -->
		{#if hasSearched && !isSearching}
			<div class="w-full max-w-3xl mt-8 animate-fade-in-up text-left mb-20" dir="auto">
				
				{#if searchMode === 'workspace'}
					<div class="text-sm text-gray-400 mb-6 font-mono">Found {filteredProjects.length} matching workspace projects</div>
					
					<div class="flex flex-col gap-6">
						{#each filteredProjects as project}
							<div class="p-5 bg-white border border-gray-200 rounded-xl shadow-sm hover:border-emerald-300 transition group flex flex-col">
								<div class="flex justify-between items-start mb-2">
									<span class="text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">Study Project</span>
									{#if project.teacher_name}
										<span class="text-xs font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Teacher: {project.teacher_name}</span>
									{/if}
								</div>
								<a href="/reader?project_id={project.id}" class="text-lg font-bold text-emerald-800 hover:underline mb-1">
									{project.title}
								</a>
								<p class="text-gray-600 text-sm">{project.description || 'No description provided.'}</p>
								<div class="text-xs text-gray-400 mt-4 border-t pt-3 flex justify-between">
									<span>Created {new Date(project.created_at).toLocaleDateString()}</span>
									<span class="font-bold text-emerald-600 group-hover:underline">Open in Notebook →</span>
								</div>
							</div>
						{:else}
							<p class="text-center text-gray-400 py-8">No matching notes or study projects found in your workspace.</p>
						{/each}
					</div>
				{:else}
					<div class="text-sm text-gray-400 mb-6 font-mono">{t.results}</div>
					
					<div class="flex flex-col gap-8">
						<!-- Match library books first -->
						{#each filteredBooks as book}
							<div class="p-5 bg-white border border-gray-200 rounded-xl shadow-sm hover:border-emerald-300 transition flex gap-4 items-center justify-between">
								<div>
									<div class="flex items-center gap-2 mb-1">
										<span class="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">Library Book</span>
										<span class="text-sm text-gray-500">{book.author_name || 'Classical Scholar'}</span>
									</div>
									<h3 class="text-lg font-bold text-gray-900">{book.title}</h3>
								</div>
								<a href="/books" class="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-4 py-2 rounded-lg text-xs transition shrink-0 shadow">
									Open Library
								</a>
							</div>
						{/each}

						<!-- Standard Semantic/Mock results -->
						{#each mockResults as result}
							<div class="group">
								<div class="flex items-center gap-2 mb-1">
									<span class="text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">{result.type}</span>
									<span class="text-sm text-gray-500">{result.author}</span>
								</div>
								<a href="/books" class="text-xl font-medium text-emerald-800 hover:underline mb-1 block dir-auto">
									{result.title}
								</a>
								<p class="text-gray-600 leading-relaxed text-sm" dir="auto">
									{@html result.context}
								</p>
								<div class="flex gap-2 mt-2">
									{#each result.tags as tag}
										<span class="text-xs text-emerald-600 font-medium">#{tag}</span>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</main>

<style>
	.animate-fade-in-up {
		animation: fadeInUp 0.5s ease-out forwards;
	}
	@keyframes fadeInUp {
		from { opacity: 0; transform: translateY(10px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
