// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://banatic.github.io',
	base: '/acww-wiki',
	integrations: [
		starlight({
			title: '놀러오세요 동물의 숲 코드 검증 위키',
			locales: { root: { label: '한국어', lang: 'ko' } },
		}),
	],
});
