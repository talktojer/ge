import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import styled, { keyframes, createGlobalStyle } from 'styled-components';
import { useAppSelector } from '../../hooks/redux';

// Game effects context
interface GameEffectsContextType {
  playSound: (soundName: string, volume?: number) => void;
  triggerAnimation: (animationType: string, target?: string) => void;
  showParticleEffect: (effectType: string, position: { x: number; y: number }) => void;
  setAmbientMusic: (trackName: string) => void;
  enableEffects: boolean;
  setEnableEffects: (enabled: boolean) => void;
}

const GameEffectsContext = createContext<GameEffectsContextType | undefined>(undefined);

// Sound effects mapping
const SOUND_EFFECTS = {
  weapon_fire: '/sounds/weapon_fire.mp3',
  explosion: '/sounds/explosion.mp3',
  shield_hit: '/sounds/shield_hit.mp3',
  engine_start: '/sounds/engine_start.mp3',
  warp_jump: '/sounds/warp_jump.mp3',
  notification: '/sounds/notification.mp3',
  error: '/sounds/error.mp3',
  success: '/sounds/success.mp3',
  scanner_ping: '/sounds/scanner_ping.mp3',
  mine_deploy: '/sounds/mine_deploy.mp3',
  spy_deploy: '/sounds/spy_deploy.mp3',
  cloak_activate: '/sounds/cloak_activate.mp3',
  target_lock: '/sounds/target_lock.mp3',
  incoming_message: '/sounds/incoming_message.mp3',
  critical_alert: '/sounds/critical_alert.mp3',
};

// Particle effects animations
const particleExplosion = keyframes`
  0% {
    opacity: 1;
    transform: scale(0) rotate(0deg);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.5) rotate(180deg);
  }
  100% {
    opacity: 0;
    transform: scale(2) rotate(360deg);
  }
`;

const energyPulse = keyframes`
  0% {
    opacity: 0.3;
    transform: scale(1);
    box-shadow: 0 0 10px rgba(74, 222, 128, 0.3);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
    box-shadow: 0 0 20px rgba(74, 222, 128, 0.8);
  }
  100% {
    opacity: 0.3;
    transform: scale(1);
    box-shadow: 0 0 10px rgba(74, 222, 128, 0.3);
  }
`;

const weaponTrail = keyframes`
  0% {
    width: 0%;
    opacity: 1;
  }
  70% {
    width: 100%;
    opacity: 1;
  }
  100% {
    width: 100%;
    opacity: 0;
  }
`;

const shieldFlash = keyframes`
  0% {
    background: rgba(96, 165, 250, 0);
    border-color: rgba(96, 165, 250, 0);
  }
  50% {
    background: rgba(96, 165, 250, 0.3);
    border-color: rgba(96, 165, 250, 0.8);
  }
  100% {
    background: rgba(96, 165, 250, 0);
    border-color: rgba(96, 165, 250, 0);
  }
`;

const scannerSweep = keyframes`
  0% {
    transform: rotate(0deg);
    opacity: 0.8;
  }
  100% {
    transform: rotate(360deg);
    opacity: 0.3;
  }
`;

const warpJump = keyframes`
  0% {
    transform: scale(1) translateX(0);
    opacity: 1;
  }
  50% {
    transform: scale(0.1) translateX(200px);
    opacity: 0.5;
  }
  100% {
    transform: scale(1) translateX(400px);
    opacity: 0;
  }
`;

// Global styles for enhanced visual effects
const GlobalEffectsStyles = createGlobalStyle<{ enableEffects: boolean }>`
  ${props => props.enableEffects && `
    /* Enhanced button hover effects */
    button {
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    button:active {
      transform: translateY(0);
      transition: all 0.1s ease;
    }
    
    /* Enhanced card animations */
    [data-card] {
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    [data-card]:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    }
    
    /* Tactical display enhancements */
    [data-tactical-object] {
      transition: all 0.2s ease;
      filter: drop-shadow(0 0 4px currentColor);
    }
    
    [data-tactical-object]:hover {
      filter: drop-shadow(0 0 8px currentColor);
      transform: scale(1.1);
    }
    
    /* Status bar animations */
    [data-status-bar] {
      transition: all 0.5s ease;
    }
    
    /* Enhanced text effects */
    [data-glow-text] {
      text-shadow: 0 0 10px currentColor;
      animation: ${energyPulse} 2s ease-in-out infinite;
    }
    
    /* Combat effect overlays */
    .combat-flash {
      animation: ${shieldFlash} 0.3s ease-out;
    }
    
    .weapon-trail {
      animation: ${weaponTrail} 0.5s linear;
    }
    
    .scanner-sweep {
      animation: ${scannerSweep} 4s linear infinite;
    }
    
    .warp-effect {
      animation: ${warpJump} 1s ease-in-out;
    }
  `}
`;

// Particle effect components
const ParticleContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 9999;
`;

const Particle = styled.div<{ 
  x: number; 
  y: number; 
  type: string;
  delay: number;
}>`
  position: absolute;
  left: ${props => props.x}px;
  top: ${props => props.y}px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: ${props => {
    switch (props.type) {
      case 'explosion': return '#ff6b6b';
      case 'energy': return '#4ecdc4';
      case 'spark': return '#ffe66d';
      case 'smoke': return '#95a5a6';
      default: return '#fff';
    }
  }};
  animation: ${particleExplosion} 1s ease-out ${props => props.delay}ms forwards;
`;

const ScreenFlash = styled.div<{ color: string; duration: number }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: ${props => props.color};
  pointer-events: none;
  z-index: 9998;
  animation: flash ${props => props.duration}ms ease-out;
  
  @keyframes flash {
    0% { opacity: 0; }
    50% { opacity: 0.3; }
    100% { opacity: 0; }
  }
`;

// Audio manager
class AudioManager {
  private audioContext: AudioContext | null = null;
  private sounds: Map<string, AudioBuffer> = new Map();
  private ambientMusic: HTMLAudioElement | null = null;
  private masterVolume = 0.7;
  private soundVolume = 0.8;
  private musicVolume = 0.4;

  constructor() {
    this.initializeAudioContext();
  }

  private initializeAudioContext() {
    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    } catch (error) {
      console.warn('Web Audio API not supported:', error);
    }
  }

  async loadSound(name: string, url: string): Promise<void> {
    if (!this.audioContext) return;

    try {
      const response = await fetch(url);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      this.sounds.set(name, audioBuffer);
    } catch (error) {
      console.warn(`Failed to load sound ${name}:`, error);
    }
  }

  playSound(name: string, volume: number = 1): void {
    if (!this.audioContext || !this.sounds.has(name)) return;

    try {
      const audioBuffer = this.sounds.get(name)!;
      const source = this.audioContext.createBufferSource();
      const gainNode = this.audioContext.createGain();
      
      source.buffer = audioBuffer;
      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      gainNode.gain.value = this.masterVolume * this.soundVolume * volume;
      source.start();
    } catch (error) {
      console.warn(`Failed to play sound ${name}:`, error);
    }
  }

  setAmbientMusic(trackName: string): void {
    if (this.ambientMusic) {
      this.ambientMusic.pause();
      this.ambientMusic = null;
    }

    if (trackName) {
      this.ambientMusic = new Audio(`/music/${trackName}.mp3`);
      this.ambientMusic.loop = true;
      this.ambientMusic.volume = this.masterVolume * this.musicVolume;
      this.ambientMusic.play().catch(error => {
        console.warn('Failed to play ambient music:', error);
      });
    }
  }

  setMasterVolume(volume: number): void {
    this.masterVolume = Math.max(0, Math.min(1, volume));
    if (this.ambientMusic) {
      this.ambientMusic.volume = this.masterVolume * this.musicVolume;
    }
  }
}

// Particle effect manager
interface ParticleEffect {
  id: string;
  type: string;
  x: number;
  y: number;
  particles: Array<{
    x: number;
    y: number;
    delay: number;
    type: string;
  }>;
  duration: number;
}

const GameEffectsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [enableEffects, setEnableEffects] = useState(true);
  const [particles, setParticles] = useState<ParticleEffect[]>([]);
  const [screenFlash, setScreenFlash] = useState<{ color: string; duration: number } | null>(null);
  
  const audioManagerRef = useRef<AudioManager>(new AudioManager());
  const gameUpdates = useAppSelector(state => state.game.updates);

  // Initialize audio effects
  useEffect(() => {
    const audioManager = audioManagerRef.current;
    
    // Load sound effects
    Object.entries(SOUND_EFFECTS).forEach(([name, url]) => {
      audioManager.loadSound(name, url);
    });

    // Set initial ambient music
    audioManager.setAmbientMusic('space_ambient');
  }, []);

  // Handle game events for automatic effects
  useEffect(() => {
    const latestUpdate = gameUpdates[gameUpdates.length - 1];
    if (!latestUpdate || !enableEffects) return;

    switch (latestUpdate.type) {
      case 'combat_event':
        if (latestUpdate.data.type === 'weapon_fire') {
          playSound('weapon_fire');
          showParticleEffect('weapon_trail', { x: 400, y: 300 });
        } else if (latestUpdate.data.type === 'explosion') {
          playSound('explosion');
          showParticleEffect('explosion', { x: 400, y: 300 });
          triggerScreenFlash('rgba(255, 107, 107, 0.3)', 200);
        } else if (latestUpdate.data.type === 'shield_hit') {
          playSound('shield_hit');
          triggerScreenFlash('rgba(96, 165, 250, 0.2)', 150);
        }
        break;

      case 'wormhole_travel':
        playSound('warp_jump');
        triggerAnimation('warp_effect');
        break;

      case 'spy_report':
        playSound('notification');
        break;

      case 'mine_triggered':
        playSound('explosion');
        showParticleEffect('explosion', { x: 200, y: 200 });
        triggerScreenFlash('rgba(255, 107, 107, 0.4)', 300);
        break;

      case 'tactical_scan':
        playSound('scanner_ping');
        break;

      default:
        break;
    }
  }, [gameUpdates, enableEffects]);

  const playSound = (soundName: string, volume: number = 1) => {
    if (!enableEffects) return;
    audioManagerRef.current.playSound(soundName, volume);
  };

  const triggerAnimation = (animationType: string, target?: string) => {
    if (!enableEffects) return;
    
    const elements = target ? document.querySelectorAll(target) : document.querySelectorAll('[data-animate]');
    elements.forEach(element => {
      element.classList.add(animationType);
      setTimeout(() => {
        element.classList.remove(animationType);
      }, 1000);
    });
  };

  const showParticleEffect = (effectType: string, position: { x: number; y: number }) => {
    if (!enableEffects) return;

    const particleCount = effectType === 'explosion' ? 20 : 10;
    const particleEffect: ParticleEffect = {
      id: Date.now().toString(),
      type: effectType,
      x: position.x,
      y: position.y,
      particles: Array.from({ length: particleCount }, (_, i) => ({
        x: position.x + (Math.random() - 0.5) * 100,
        y: position.y + (Math.random() - 0.5) * 100,
        delay: i * 50,
        type: effectType
      })),
      duration: 1000
    };

    setParticles(prev => [...prev, particleEffect]);

    setTimeout(() => {
      setParticles(prev => prev.filter(p => p.id !== particleEffect.id));
    }, particleEffect.duration + 500);
  };

  const triggerScreenFlash = (color: string, duration: number) => {
    if (!enableEffects) return;

    setScreenFlash({ color, duration });
    setTimeout(() => {
      setScreenFlash(null);
    }, duration);
  };

  const setAmbientMusic = (trackName: string) => {
    if (!enableEffects) return;
    audioManagerRef.current.setAmbientMusic(trackName);
  };

  const contextValue: GameEffectsContextType = {
    playSound,
    triggerAnimation,
    showParticleEffect,
    setAmbientMusic,
    enableEffects,
    setEnableEffects
  };

  return (
    <GameEffectsContext.Provider value={contextValue}>
      <GlobalEffectsStyles enableEffects={enableEffects} />
      
      {/* Particle effects overlay */}
      {enableEffects && (
        <ParticleContainer>
          {particles.map(effect => (
            effect.particles.map((particle, i) => (
              <Particle
                key={`${effect.id}-${i}`}
                x={particle.x}
                y={particle.y}
                type={particle.type}
                delay={particle.delay}
              />
            ))
          ))}
        </ParticleContainer>
      )}

      {/* Screen flash effects */}
      {enableEffects && screenFlash && (
        <ScreenFlash color={screenFlash.color} duration={screenFlash.duration} />
      )}

      {children}
    </GameEffectsContext.Provider>
  );
};

// Custom hook to use game effects
export const useGameEffects = (): GameEffectsContextType => {
  const context = useContext(GameEffectsContext);
  if (!context) {
    throw new Error('useGameEffects must be used within a GameEffectsProvider');
  }
  return context;
};

export default GameEffectsProvider;
