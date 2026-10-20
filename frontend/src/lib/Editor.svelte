<script lang="ts">
	import { onMount } from 'svelte';

	let { noteContent = $bindable('') } = $props();
	let parsedContent = $state('');
	let isResolving = $state(false);

	// Mock function to simulate backend @mention resolution
	async function resolveMentions() {
		isResolving = true;
		
		// Regex to find @surah:ayah or bukhari:num
		const mentionRegex = /(@\d+:\d+|bukhari:\d+)/g;
		let htmlContent = noteContent;

		const mentions = noteContent.match(mentionRegex);
		
		if (mentions) {
			for (const mention of mentions) {
				// Simulate API delay
				await new Promise(resolve => setTimeout(resolve, 500));
				
				let cardHtml = '';
				if (mention === '@2:255') {
					cardHtml = `
						<div contenteditable="false" class="my-2 p-4 bg-emerald-50 border border-emerald-200 rounded-lg shadow-sm" dir="rtl">
							<p class="text-xl text-emerald-900 font-bold font-arabic mb-2 leading-loose">اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...</p>
							<p class="text-sm text-gray-600 mb-2" dir="ltr">Allah! There is no deity except Him, the Ever-Living, the Sustainer of [all] existence...</p>
							<div class="flex justify-between items-center mt-2 pt-2 border-t border-emerald-100">
								<span class="text-xs text-emerald-700 font-bold">Surah Al-Baqarah (2:255)</span>
								<span class="text-xs bg-emerald-200 text-emerald-800 px-2 py-1 rounded">Quran</span>
							</div>
						</div>
					`;
				} else if (mention === 'bukhari:1') {
					cardHtml = `
						<div contenteditable="false" class="my-2 p-4 bg-blue-50 border border-blue-200 rounded-lg shadow-sm" dir="rtl">
							<p class="text-lg text-blue-900 font-bold font-arabic mb-2 leading-loose">إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى...</p>
							<p class="text-sm text-gray-600 mb-2" dir="ltr">The reward of deeds depends upon the intentions and every person will get the reward according to what he has intended...</p>
							<div class="flex justify-between items-center mt-2 pt-2 border-t border-blue-100">
								<span class="text-xs text-blue-700 font-bold">Sahih al-Bukhari 1</span>
								<span class="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">Hadith</span>
							</div>
						</div>
					`;
				} else {
					cardHtml = `<span class="bg-yellow-100 text-yellow-800 px-1 rounded animate-pulse">Resolving ${mention}...</span>`;
				}
				
				htmlContent = htmlContent.replace(mention, cardHtml);
			}
		}

		parsedContent = htmlContent;
		isResolving = false;
	}

	function handleInput(event: Event) {
		const target = event.target as HTMLTextAreaElement;
		noteContent = target.value;
		// Simple debounce for resolution
		clearTimeout((window as any).resolveTimeout);
		(window as any).resolveTimeout = setTimeout(resolveMentions, 1000);
	}
</script>

<div class="flex flex-col gap-4">
	<div class="flex justify-between items-center mb-2">
		<h3 class="font-bold text-gray-700">Notebook Editor</h3>
		{#if isResolving}
			<span class="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded animate-pulse">Fetching References...</span>
		{/if}
	</div>
	
	<!-- Raw Input Area -->
	<textarea 
		class="w-full h-32 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none resize-none font-arabic text-lg" 
		dir="rtl" 
		placeholder="اكتب ملاحظاتك هنا... جرب كتابة @2:255 أو bukhari:1"
		oninput={handleInput}
		bind:value={noteContent}
	></textarea>

	<!-- Rich Rendered Output Area -->
	{#if parsedContent}
		<div class="mt-4 border-t pt-4">
			<h4 class="text-xs text-gray-400 uppercase tracking-wider mb-3">Live Preview (Smart Mentions)</h4>
			<div class="w-full min-h-32 p-4 bg-white border border-gray-200 shadow-inner rounded-lg font-arabic text-lg leading-relaxed" dir="rtl">
				{@html parsedContent}
			</div>
		</div>
	{/if}
</div>

