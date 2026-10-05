// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://banatic.github.io',
	base: '/acww-wiki',
	integrations: [
		starlight({
			title: '놀러오세요 동물의 숲 위키',
			favicon: '/favicon.ico',
			locales: { root: { label: '한국어', lang: 'ko' } },
			head: [{ tag: 'link', attrs: { rel: 'stylesheet', crossorigin: '', href: 'https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css' } }, { tag: 'link', attrs: { rel: 'stylesheet', href: '/acww-wiki/wiki.css' } }, { tag: 'link', attrs: { rel: 'stylesheet', href: '/acww-wiki/home/home-calendar.css' } }, { tag: 'script', attrs: { src: '/acww-wiki/home/home-calendar.js', defer: true } }, { tag: 'script', attrs: { src: '/acww-wiki/home/home-walkers.js', defer: true } }],
		}),
	],
});
