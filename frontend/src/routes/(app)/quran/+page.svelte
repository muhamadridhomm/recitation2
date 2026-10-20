<script lang="ts">
	import { onMount } from 'svelte';

	let surahs = $state<any[]>([]);
	let selectedSurah = $state<any>(null);
	let verses = $state<any[]>([]);
	let isLoadingSurahs = $state(false);
	let isLoadingVerses = $state(false);
	let searchQuery = $state('');

	onMount(async () => {
		await loadSurahs();
	});

	async function loadSurahs() {
		isLoadingSurahs = true;
		try {
			const res = await fetch('https://api.alquran.cloud/v1/surah');
			if (res.ok) {
				const data = await res.json();
				surahs = data.data;
			}
		} catch (err) {
			console.error("Error loading Quran surahs:", err);
		} finally {
			isLoadingSurahs = false;
		}
	}

	async function selectSurah(surah: any) {
		selectedSurah = surah;
		isLoadingVerses = true;
		verses = [];
		try {
			// Fetch Arabic, English and Indonesian editions aligned together
			const res = await fetch(`https://api.alquran.cloud/v1/surah/${surah.number}/editions/quran-uthmani,en.sahih,id.indonesian`);
			if (res.ok) {
				const data = await res.json();
				const arabicEd = data.data[0].ayahs;
				const englishEd = data.data[1].ayahs;
				const indoEd = data.data[2].ayahs;

				const aligned = arabicEd.map((ayah: any, index: number) => ({
					numberInSurah: ayah.numberInSurah,
					text: ayah.text,
					english: englishEd[index]?.text || '',
					indonesian: indoEd[index]?.text || ''
				}));
				verses = aligned;
			}
		} catch (err) {
			console.error("Error loading Quran verses:", err);
		} finally {
			isLoadingVerses = false;
		}
	}

	let filteredSurahs = $derived(
		surahs.filter(s => 
			s.englishName.toLowerCase().includes(searchQuery.toLowerCase()) ||
			s.englishNameTranslation.toLowerCase().includes(searchQuery.toLowerCase()) ||
			s.number.toString() === searchQuery
		)
	);
</script>

<svelte:head>
	<title>Al-Qur'an - Islamic Notes</title>
</svelte:head>

	<!-- Main Workspace Split Panel -->
	<div class="flex-1 flex overflow-hidden h-full">
		
		<!-- Left Panel: Surah List -->
		<aside class="w-80 border-r border-gray-200 bg-white flex flex-col shrink-0 h-full">
			<div class="p-4 border-b border-gray-100">
				<input 
					type="text" 
					bind:value={searchQuery} 
					placeholder="Search surahs by name or number..." 
					class="w-full p-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition"
				/>
			</div>

			<div class="flex-1 overflow-y-auto divide-y divide-gray-50">
				{#if isLoadingSurahs}
					<div class="flex justify-center p-8">
						<svg class="animate-spin h-6 w-6 text-emerald-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
					</div>
				{:else}
					{#each filteredSurahs as surah}
						<button 
							onclick={() => selectSurah(surah)} 
							class="w-full text-left p-4 hover:bg-emerald-50/50 transition flex justify-between items-center {selectedSurah?.number === surah.number ? 'bg-emerald-50 border-l-4 border-emerald-600' : ''}"
						>
							<div class="flex items-center gap-3">
								<span class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-mono font-bold text-gray-500">{surah.number}</span>
								<div>
									<h4 class="font-bold text-gray-900 text-sm">{surah.englishName}</h4>
									<p class="text-xs text-gray-400 font-medium">{surah.englishNameTranslation} • {surah.numberOfAyahs} Ayat</p>
								</div>
							</div>
							<span class="font-arabic text-lg text-emerald-800 font-bold">{surah.name}</span>
						</button>
					{/each}
				{/if}
			</div>
		</aside>

		<!-- Right Panel: Verses Canvas -->
		<main class="flex-1 bg-gray-50 overflow-y-auto p-6 md:p-10 flex flex-col">
			{#if selectedSurah}
				<div class="max-w-4xl mx-auto w-full">
					<!-- Surah Header Header Card -->
					<div class="bg-gradient-to-r from-emerald-800 to-emerald-950 rounded-2xl p-8 text-white shadow-lg mb-8 text-center relative overflow-hidden">
						<div class="absolute -right-10 -bottom-10 opacity-10 font-arabic text-8xl">{selectedSurah.name}</div>
						<h2 class="text-2xl md:text-3xl font-extrabold mb-1">{selectedSurah.englishName}</h2>
						<p class="text-emerald-300 text-sm font-semibold tracking-wider uppercase mb-4">{selectedSurah.englishNameTranslation} • {selectedSurah.revelationType}</p>
						<hr class="border-emerald-700/50 max-w-xs mx-auto mb-4" />
						
						<!-- Bismillah placeholder (skip for Surah 9 At-Tawbah) -->
						{#if selectedSurah.number !== 9}
							<div class="font-arabic text-2xl tracking-wide font-medium mt-2">بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ</div>
						{/if}
					</div>

					<!-- Verses List -->
					<div class="flex flex-col gap-6">
						{#if isLoadingVerses}
							<div class="flex justify-center p-12">
								<svg class="animate-spin h-8 w-8 text-emerald-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
							</div>
						{:else}
							{#each verses as verse}
								<div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:border-emerald-200 transition flex flex-col gap-4">
									<div class="flex justify-between items-center text-xs text-gray-400 font-mono border-b pb-2">
										<span>Ayah {verse.numberInSurah}</span>
										<span class="font-bold text-emerald-700">Surah {selectedSurah.number} : {verse.numberInSurah}</span>
									</div>
									
									<!-- Arabic Text -->
									<div class="font-arabic text-3xl text-gray-900 leading-relaxed text-right py-4" dir="rtl">
										{verse.text}
									</div>

									<!-- Translations -->
									<div class="flex flex-col gap-2 border-t pt-4 text-sm text-gray-600 font-sans">
										<p><strong class="text-xs font-bold text-indigo-700 uppercase tracking-wide mr-1">EN:</strong> {verse.english}</p>
										<p><strong class="text-xs font-bold text-emerald-700 uppercase tracking-wide mr-1">ID:</strong> {verse.indonesian}</p>
									</div>
								</div>
							{/each}
						{/if}
					</div>
				</div>
			{:else}
				<div class="flex-1 flex flex-col items-center justify-center text-center text-gray-400 p-8">
					<svg class="w-16 h-16 text-emerald-200 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
					<h3 class="font-bold text-gray-700 text-lg mb-1">Select a Surah</h3>
					<p class="text-sm max-w-xs">Select a Surah from the left panel to begin reading the Al-Qur'an text with side-by-side translations.</p>
				</div>
			{/if}
		</main>
	</div>
