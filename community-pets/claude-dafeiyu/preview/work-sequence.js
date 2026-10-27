var PetWorkSequence = (function(exports) {

"use strict";

//#region ../../.tools/companion-runtime/20261027-151746/stage/src/shared/pickers.ts
const pick = (pool, exclude) => {
	const entries = exclude ? pool.filter((n) => n !== exclude) : pool;
	const src = entries.length ? entries : pool;
	return src[Math.floor(Math.random() * src.length)];
};

//#endregion
//#region ../../.tools/companion-runtime/20261027-151746/stage/src/shared/work-sequence.ts
function advanceWorkSequence(sequence, phase, state, current, ended = false) {
	if (!sequence) return {
		phase,
		name: null,
		handled: false
	};
	const working = !!state && state !== "success" && state !== "error";
	if (phase === "opening" && current !== sequence.enter) return working ? {
		phase: "opening",
		name: sequence.enter,
		handled: true
	} : {
		phase: "closing",
		name: sequence.exit,
		handled: true
	};
	if (phase === "closing" && current !== sequence.exit) return working ? {
		phase: "opening",
		name: sequence.enter,
		handled: true
	} : {
		phase: "closed",
		name: null,
		handled: false
	};
	if (phase === "opening" && !ended) return {
		phase,
		name: null,
		handled: true
	};
	if (phase === "closing") {
		if (!ended) return {
			phase,
			name: null,
			handled: true
		};
		phase = "closed";
	}
	if (working) {
		if (phase === "closed") return {
			phase: "opening",
			name: sequence.enter,
			handled: true
		};
		if (phase === "open" && !ended && sequence.loops.includes(current)) return {
			phase,
			name: null,
			handled: true
		};
		return {
			phase: "open",
			name: pick(sequence.loops, current),
			handled: true
		};
	}
	if (phase === "open" || phase === "opening") return {
		phase: "closing",
		name: sequence.exit,
		handled: true
	};
	return {
		phase: "closed",
		name: null,
		handled: false
	};
}
function isWorkSequenceAnim(sequence, name) {
	return !!sequence && (name === sequence.enter || name === sequence.exit || sequence.loops.includes(name));
}

//#endregion
exports.advanceWorkSequence = advanceWorkSequence
exports.isWorkSequenceAnim = isWorkSequenceAnim
return exports;
})({});