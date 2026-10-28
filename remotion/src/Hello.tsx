import {AbsoluteFill, Audio, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export const Hello: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame: frame - 5, fps, config: {damping: 14}});
	return (
		<AbsoluteFill style={{background: '#0b0b10', justifyContent: 'center', alignItems: 'center'}}>
			<Audio src={staticFile('whoosh-1.wav')} />
			<h1
				style={{
					color: 'white',
					fontFamily: 'sans-serif',
					fontSize: 120,
					transform: `translateY(${interpolate(s, [0, 1], [120, 0])}px) scale(${s})`,
					opacity: s,
				}}
			>
				Remotion ready
			</h1>
		</AbsoluteFill>
	);
};
